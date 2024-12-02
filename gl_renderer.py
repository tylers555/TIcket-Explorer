
# import glfw
from OpenGL.GL import *  # pylint: disable=W0614
from OpenGL.GLU import *
from PySide6.QtCore import QSize
from PySide6.QtWidgets import *
from PySide6.QtOpenGLWidgets import *

import glm
import numpy

from datetime import datetime
import time

import threading

g_vertex_buffer_data = [
        0,   0,   0,  -1, -1, -1,
    300,   0,   0,   1, -1, -1,
    300, 300,   0,   1,  1, -1,
        0, 300,   0,  -1,  1, -1,
        0,   0, 300,  -1, -1,  1,
    300,   0, 300,   1, -1,  1,
    300, 300, 300,   1,  1,  1,
        0, 300, 300,  -1,  1,  1,
]
g_element_buffer_data = [
    0, 1, 3,  1, 2, 3,
    3, 2, 7,  2, 6, 7,
    1, 5, 2,  5, 6, 2,
    5, 4, 6,  4, 7, 6,
    4, 0, 7,  0, 3, 7,
    4, 5, 0,  5, 1, 0,
]
# g_color_buffer_data = [ 
# 		1.0, 0.0, 0.0,
#         1.0, 0.0, 0.0,
#         0.0, 0.0, 1.0,
#         0.0, 0.0, 1.0,
#         1.0, 1.0, 0.0,
#         1.0, 1.0, 0.0,
#         0.0, 1.0, 0.0,
#         0.0, 1.0, 0.0,
# ]

# g_vertex_buffer_data = [i / 50.0 for i in g_vertex_buffer_data]
VERTEX_SOURCE = """#version 330 core

// Input vertex data, different for all executions of this shader.
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;

// Values that stay constant for the whole mesh.
uniform mat4 uModel;
uniform mat4 uMVP;
uniform vec3 uColor;

out vec3 FragPos;
out vec3 FragNormal;
out vec3 FragColor;

void main(){	
    FragPos    = vec3(uModel * vec4(aPos, 1));
    FragNormal = mat3(transpose(inverse(uModel)))*aNormal;

    // FragColor = aNormal;
    FragColor = uColor;
    // FragColor = FragNormal;
	gl_Position = uMVP * vec4(aPos,1);
}"""
FRAGMENT_SOURCE = """#version 330 core

// in vec3 FragColor;
in vec3 FragPos;
in vec3 FragNormal; 
in vec3 FragColor;

// Ouput data
out vec4 OutColor;

uniform vec3 uCamPos;

void main(){
#if 1
    vec3 lightPos = vec3(800, 800, 800);
    vec3 lightDir = normalize(lightPos - FragPos);
    vec3 lightColor = vec3(1.0, 1.0, 1.0);
    vec3 ambient = 0.5*lightColor;
    
    vec3 norm = normalize(FragNormal);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * lightColor;
#else
    vec3 lightColor = vec3(1.0, 1.0, 1.0);
    vec3 ambient = 0.7*lightColor;
    vec3 diffuse = 0.0*lightColor;
#endif
    
	vec3 color = (ambient + diffuse) * FragColor;
    // vec3 color = FragColor;
    // vec3 color = norm;
    // vec3 color = vec3(1.0, 0.0, 0.0);
    
    OutColor = vec4(color, 1.0);
    // color = norm;

}"""

program = None

def print_gl_error():
    err = glGetError()
    if (err != GL_NO_ERROR):
        print('GLERROR: ', gluErrorString(err))

class GLShaderProgram:
    def __init__(self, vertex_source, fragment_source, geometry_source=None):        
        program = glCreateProgram()
        print_gl_error()

        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, [vertex_source])
        glCompileShader(vs)
        if glGetShaderiv(vs, GL_COMPILE_STATUS) != GL_TRUE:
            err = glGetShaderInfoLog(vs)
            raise Exception(err.decode())
        glAttachShader(program, vs)
        print_gl_error()
        
        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, [fragment_source])
        glCompileShader(fs)
        if glGetShaderiv(fs, GL_COMPILE_STATUS) != GL_TRUE:
            err = glGetShaderInfoLog(fs)
            raise Exception(err.decode())
        glAttachShader(program, fs)
        print_gl_error()

        if geometry_source:
            gs = glCreateShader(GL_GEOMETRY_SHADER)
            glShaderSource(gs, [geometry_source])
            glCompileShader(gs)
            if glGetShaderiv(gs, GL_COMPILE_STATUS) != GL_TRUE:
                err = glGetShaderInfoLog(gs)
                raise Exception(err.decode())
            glAttachShader(program, gs)
            print_gl_error()


        glLinkProgram(program)
        if glGetProgramiv(program, GL_LINK_STATUS) != GL_TRUE:
            err = glGetProgramInfoLog(program)
            raise Exception(err.decode())
        
        self.program  = program
        glUseProgram(self.program)
        self.MODEL_ID = glGetUniformLocation(self.program,"uModel")
        self.MVP_ID   = glGetUniformLocation(self.program,"uMVP")
        self.COLOR_ID = glGetUniformLocation(self.program,"uColor")
    
    def use(self):
        glUseProgram(self.program)
    
    def set_color(self, color):
        glUniform3fv(self.COLOR_ID, 1, glm.value_ptr(color))

    def set_mvp(self, aspect, pos, angle, cam_pos=glm.vec3(0, 300, 300)):
        self.use()
        proj = glm.perspective(
            glm.radians(50),
            aspect,
            0.1,
            1000.0)
        view =  glm.lookAt(cam_pos, # Camera is at
                           glm.vec3(0,0,0), #looks at the (0.0.0))
                           glm.vec3(0,0,1))

        model = glm.mat4(1.0)
        model = glm.rotate(model, glm.radians(angle), glm.vec3(0, 0, 1))
        model = glm.translate(model, -pos)
        mvp =  proj * view * model

        glUniformMatrix4fv(self.MODEL_ID,1,GL_FALSE,glm.value_ptr(model))
        glUniformMatrix4fv(self.MVP_ID,1,GL_FALSE,glm.value_ptr(mvp))


class GLModel:
    def __init__(self, model):
        self.vertex_array   = -1
        self.vertex_buffer  = -1
        self.element_buffer = -1
        if not model:
            return
        self.vertices = model.vertices
        self.indices = model.indices
        self.center = model.center
        self.num_elements = model.indices.size

        self.width  = model.max_x
        self.length = model.max_y
        self.height = model.max_z
        self.element_buffer = 0

    def finalize(self):
        if self.vertex_array >= 0:
            return

        self.vertex_array = glGenVertexArrays(1)
        glBindVertexArray(self.vertex_array)

        self.vertex_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,24,None)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,24,ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        self.element_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.element_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices, GL_STATIC_DRAW)

        self.vertices = None
        self.indices  = None

        glBindVertexArray(0)
        # print(f"# elements: {self.num_elements}")

    def __del__(self):
        if self.vertex_array >= 0:
            glDeleteBuffers(1, [self.vertex_buffer])
            glDeleteBuffers(1, [self.element_buffer])
            glDeleteVertexArrays(1, [self.vertex_array])
        self.vertex_array = -1

    def draw(self):
        if self.vertex_array >= 0:
            self.finalize()
            glBindVertexArray(self.vertex_array)
            # glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.element_buffer)
            glDrawElements(GL_TRIANGLES, self.num_elements, GL_UNSIGNED_INT, None) 

class GLModelLoader:
    def __init__(self, ticket, update_status):
        self.ticket = ticket
        self.update_status = update_status
        self.model = None
        
        threading.Thread(target=self.thread_load_ticket).start()

    def thread_load_ticket(self):
        if not self.ticket.gl_model:
            self.update_status("Parsing model")
            model = self.ticket.get_model()
            if not model:
                print("Issue parsing model!")
            self.model = model

    def is_ready(self):
        if self.ticket.gl_model:
            return True
        elif self.model:
            self.update_status("Loading model")
            gl_model = GLModel(self.model)
            gl_model.finalize()
            self.ticket.gl_model = gl_model
            self.update_status("Model loaded!")
            self.gl_model = self.ticket.gl_model
            self.model = None
        else:
            return False

class GcodePreview(QOpenGLWidget):
    def __init__(self, update_status, parent=None):
        super().__init__(parent)
        self.shader = None
        self.ticket = None
        self.model_loader = None
        self.angle = 0

        self.status = ""
        self.update_status = update_status

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def __del__(self):
        print("Better OpenGL end behavior needed!")
        pass

    def sizeHint(self) -> QSize:
        return QSize(300, 300)

    def load_ticket(self, ticket):
        self.ticket = ticket
        self.model_loader = GLModelLoader(self.ticket, self.update_status)
        self.update()

    def initializeGL(self):
        if not self.shader:
            self.shader = GLShaderProgram(VERTEX_SOURCE, FRAGMENT_SOURCE)

        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)

    def resizeGL(self, width, height):
        glViewport(0, 0, 300, 300)
        self.aspect = width/height  

    def set_color(self):
        color = glm.vec3(0.7, 0.0, 0.7)
        color_text = self.ticket.color.lower()
        if "black" in color_text:
            color = glm.vec3(0.2, 0.2, 0.2)
        elif "blue" in color_text:
            color = glm.vec3(0, 0, 1)
        elif "grey" in color_text or "gray" in color_text:
            color = glm.vec3(0.7, 0.7, 0.7)
        elif "green" in color_text:
            color = glm.vec3(0, 1, 0)
        elif "orange" in color_text:
            color = glm.vec3(1, 0.55, 0)
        elif "purple" in color_text:
            color = glm.vec3(0.3, 0, 0.5)
        elif "red" in color_text:
            color = glm.vec3(1, 0, 0)
        elif "white" in color_text:
            color = glm.vec3(1, 1, 1)
        elif "yellow" in color_text:
            color = glm.vec3(1, 1, 0)
        
        self.shader.set_color(color)
        

    def paintGL(self): 
        try:
            self.update()
            if not self.ticket: 
                return
            
            if not self.model_loader.is_ready():
                return
                
            glClearColor(0.5, 0.5, 0.5, 1.0)  
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.set_color()
            cam_pos = 1.5*glm.vec3(self.ticket.gl_model.width, self.ticket.gl_model.length, self.ticket.gl_model.height)
            self.shader.set_mvp(self.aspect, self.ticket.gl_model.center, self.angle, cam_pos)
            self.shader.use()
            self.ticket.gl_model.draw()
            self.angle += 0.5
        except:
            self.ticket = None

# def render_model(model):
#     dtime_total = 0
#     dtime_count = 0
#     time = datetime.now()
#     
#     while not glfw.window_should_close(window):
#         glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

#         

#         

#         new_time = datetime.now()
#         dtime = (new_time - time).total_seconds()
#         if dtime != 0:
#             dtime_total += dtime
#             dtime_count += 1
            
#         time = new_time

#         glfw.swap_buffers(window)
#         glfw.poll_events()

#     dtime_average = dtime_total/dtime_count 
#     print(f"Timings {1000*dtime_average:.2f} {1/dtime_average:.2f}")