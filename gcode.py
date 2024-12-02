import json
import os

import glm
import numpy as np

import tkinter as tk

import gl_renderer as render

class GCodeData:
    # volume in cubic mm3
    def __init__(self, printer, volume, material="PLA"):
        self.printer = printer
        self.weight  = (volume/1000) * 1.24
        self.material = material
        self.width  = 0
        self.length = 0
        self.height = 0

    def set_size(self, x, y, z):
        self.width  = x
        self.length = y
        self.height = z


class GCodeModel:
    def __init__(self):
        self.layer_height = 0.2
        self.current_x = None
        self.current_y = None
        self.current_z = None
        # self.figure = plt.figure()
        # self.all_x = []
        # self.all_y = []
        self.current_z = 0
        self.current_e = 0
        self.a_vertices = []
        self.b_vertices = []

        self.max_x = 0
        self.max_y = 0
        self.max_z = 0

    
    def plot_move(self, command, x, y, z, e):
        # print(self.current_layer)
        # if z and not e:
            # ax = self.figure.add_subplot(projection='3d')
            # ax.plot(self.x_coords, self.y_coords, zs=self.current_layer, zdir='z')
            # self.all_x.append(self.x_coords)
            # self.all_y.append(self.y_coords)
            # self.current_z = z
        # if self.current_layer != 100:
        #     if self.current_layer < 100:
        #         self.x_coords = []
        #         self.y_coords = []
        #     return

        # if self.index % 10 != 0:
        #     return

        old_e = self.current_e
        if e:
            self.current_e = e
            if z and abs(z-self.current_z) >= 0.01:
                self.layer_height = z-self.current_z
        if not e or e-old_e <= 0:
            if x:
                self.current_x = x
                if self.current_x > self.max_x:
                    self.max_x = self.current_x
            if y:
                self.current_y = y
                if self.current_y > self.max_y:
                    self.max_y = self.current_y
            if z:
                self.current_z = z
                if self.current_z > self.max_z:
                    self.max_z = self.current_z
            return

        old_x = self.current_x
        if not old_x:
            old_x = 0
        old_y = self.current_y
        if not old_y:
            old_y = 0
        old_z = self.current_z
        if not old_z:
            old_z = 0
        new_x = old_x
        new_y = old_y
        new_z = old_z

        if x:
            new_x = x
        if y:
            new_y = y
        if z:
            new_z = z

        valid = False
        if new_x != old_x:
            valid = (self.current_x is not None)
            self.current_x = new_x
        if new_y != old_y:  
            valid = (self.current_y is not None)
            self.current_y = new_y
        if new_z != old_z:
            valid = (self.current_z is not None)
            self.current_z = new_z

        d = glm.vec3(new_x-old_x, new_y-old_y, new_z-old_z)
        valid = valid and (glm.dot(d, d) > 0.0001)

        if valid:
            self.a_vertices.extend([[old_x, old_y, old_z]])
            self.b_vertices.extend([[new_x, new_y, new_z]])

    def done(self):
        if len(self.a_vertices) == 0:
            print("No vertices!")
            return None
        # self.x_coords = [100, 100, 200, 200, 100]
        # self.y_coords = [100, 200, 200, 100, 100]
        a = np.array(self.a_vertices, dtype=np.float32)
        b = np.array(self.b_vertices, dtype=np.float32)
        ab = b - a
        z = np.tile(np.array([[1, 1, 1]]), (len(self.a_vertices), 1))

        u = np.cross(ab, z)
        v = np.cross(ab, u)

        u_mag  = np.linalg.norm( u, axis=1)
        v_mag  = np.linalg.norm( v, axis=1)
        ab_mag = np.linalg.norm(ab, axis=1)

        u  /=  u_mag[:, np.newaxis]
        v  /=  v_mag[:, np.newaxis]
        ab /= ab_mag[:, np.newaxis]

        w = 0.4*u
        h = (self.layer_height)*v
        print(f"{self.max_x}, {self.max_y}, {self.max_z}")

        # print(w)
        # print(h)

        p0 = a - w - h
        p1 = a + w - h
        p2 = a + w + h
        p3 = a - w + h
        p4 = b - w + h
        p5 = b + w + h
        p6 = b + w - h        
        p7 = b - w - h        
        
        n0 = -ab - u - v
        n1 = -ab + u - v
        n2 = -ab + u + v
        n3 = -ab - u + v
        n4 =  ab - u + v
        n5 =  ab + u + v
        n6 =  ab + u - v        
        n7 =  ab - u - v    

        vertices = np.empty((16*len(self.a_vertices), 3), dtype=np.float32)
        vertices[0::16] = p0
        vertices[1::16] = n0
        vertices[2::16] = p1
        vertices[3::16] = n1
        vertices[4::16] = p2
        vertices[5::16] = n2
        vertices[6::16] = p3
        vertices[7::16] = n3
        vertices[8::16] = p4
        vertices[9::16] = n4
        vertices[10::16] = p5
        vertices[11::16] = n5
        vertices[12::16] = p6
        vertices[13::16] = n6
        vertices[14::16] = p7
        vertices[15::16] = n7

        indices = np.tile(np.array([[0, 1, 3, 1, 2, 3,
                                     3, 2, 4, 2, 5, 4,
                                     4, 5, 6, 4, 6, 7,
                                     7, 6, 0, 6, 1, 0,
                                     3, 4, 0, 4, 7, 0,
                                     5, 2, 6, 2, 1, 6
                                     ]], dtype=np.uint32), (len(self.a_vertices), 1))
        offsets = np.arange(0, 8*len(self.a_vertices), 8, dtype=np.uint32)
        indices += offsets[:, np.newaxis]
        # print(vertices)
        # print(indices)
        # vertices = []
        # indices  = []
        # self.model.set_data(vertices, indices)

        center = np.average(b, axis=0)
        center = glm.vec3(center[0], center[1], center[2])
        # self.model.set_center(center)
        self.vertices = vertices
        self.indices = indices
        self.center = center

def parse_gcode(path: str):
    gcode = GCodeModel() 
    current_type = None
    types = []
    printer = ""

    file = open(path)
    for line in file:
        parts = line.upper().split()
        if len(parts) == 0:
            continue
        elif parts[0][0] == ';':
            if "TYPE" in parts[0]:
                # t = parts[0].split(":")[1].strip()
                # current_type = t
                # if current_type not in types:
                #     types.append(current_type)
                pass
            elif not printer:
                if "Lulzbot" in line:
                    printer = "Lulzbot"
                elif "Ultimaker" in line:
                    printer = "Ultimaker"
                elif "ideaMaker" in line:
                    printer = "Raise3D"
                else:
                    printer = "No idea"
            continue
        elif parts[0] == 'G1' or parts[0] == 'G0':
            x_move = None
            y_move = None
            z_move = None
            e_move = None
            for i, part in enumerate(parts[1:]):
                try:
                    if ';' in part:
                        break
                    elif part[0] == 'X':
                        if part[1:]:
                            x_move = float(part[1:])
                        else:
                            x_move = float(parts[i+1])
                    elif part[0] == 'Y':
                        if part[1:]:
                            y_move = float(part[1:])
                        else:
                            y_move = float(parts[i+1])
                    elif part[0] == 'Z':
                        if part[1:]:
                            z_move = float(part[1:])
                        else:
                            z_move = float(parts[i+1])
                    elif part[0] == 'E':
                        if part[1:]:
                            e_move = float(part[1:])
                        else:
                            e_move = float(parts[i+1])
                except:
                    print(parts)

            # if current_type:
                        
                # if ("SOLID-FILL" in current_type):
                # if ("FILL" != current_type and
                #     "RAFT" != current_type):
            gcode.plot_move(parts[0],  x_move, y_move, z_move, e_move)
    file.close()
    

    gcode_data = None
    # print(types)
    # print(f"Printer: {printer}")
    # print("Done loading!")

    gcode.done()
    return gcode, gcode_data

def parse_makerbot(path: str):
    gcode = GCodeModel() 
    current_type = None
    types = []
    printer = ""

    toolpath_path = path+"/print.jsontoolpath"
    meta_path = path+"/meta.json"
    with open(toolpath_path) as file:
        data = json.load(file)
        for line in data:
            command = line["command"]
            if "function" in command.keys() and command["function"] == "move":
                parameters = command["parameters"]
                x = float(parameters["x"])
                y = float(parameters["y"])
                z = float(parameters["z"])
                e = float(parameters["a"])
                gcode.plot_move("",  x, y, z, e)

    gcode_data = None
    with open(meta_path) as file:
        data = json.load(file)
        printer = data["bot_type"]
        if printer == "replicator_5":
            printer = "Makerbot 5th Gen"
        elif printer == "replicator_b":
            printer = "Makerbot Replicator+"
        elif printer == "lava_f":
            printer = "Makerbot Method X"
        elif printer == "fire_e":
            printer = "Makerbot Method"
        volume = (2.405281875)*data["extrusion_distance_mm"]
        gcode_data = GCodeData(printer, volume)


    # print(types)
    # print(f"Printer: {printer}")
    # print("Done loading!")
    gcode.done()

    gcode_data.set_size(gcode.max_x, gcode.max_y, gcode.max_z)
    return gcode, gcode_data

def parse_model_file(path):
    model_dir, model_ext = os.path.splitext(path)
    if model_ext == ".makerbot":
        return parse_makerbot(model_dir)
    elif model_ext == ".gcode":
        return parse_gcode(path)
    else:
        return None


if __name__ == '__main__':
    # path = "C:/Users/epicr/OneDrive/Documents/webscraper_askalibrarian/files/test.gcode"
    # path = "C:/Users/epicr/OneDrive/Documents/webscraper_askalibrarian/files/13110217.gcode"
    path = "C:/Users/epicr/OneDrive/Documents/webscraper_askalibrarian/files/13008427.makerbot"
    # path = "C:/Users/epicr/OneDrive/Documents/webscraper_askalibrarian/files/13116026.gcode"
    # model = parse_gcode(path)
    model = parse_model_file(path)

    window = tk.Tk()
    window.title('3D Prints')

    gl_frame = render.TkGLFrame(model, window, width=600, height=400)
    gl_frame.pack(fill=tk.BOTH, expand=tk.YES)
    gl_frame.animate = 1
    # gl_frame.mainloop()

    window.mainloop()


    


