import re

text = """{"title":"Preview Ticket #13171627","content":"\n    \n<p style=\"font-weight: bold; font-size: 1.2em; margin-bottom:5px;\">[Reply (Admin)] Tyler Santos<\/p>\n<p style=\"font-size: .9em; margin-top: 0px;\">Feb 09 2024, 04:49PM via System<\/p>\n<div class=\"s-la-preview-reply-body\">\n    <p>\n\nThank you for using the ASU Library Makerspace 3D print submission form. We will review the file and you will be notified if there are any issues printing. Please be patient as our queue can be very busy. Priority is placed in order of school projects, self-designed models, and downloaded open-source files. For more information, check out our FAQ or schedule a 3D printing consultation.<\/p>\n<\/div>\n\n\n\n        <hr style=\"margin-top: 20px;\" \/>\n    \n<p style=\"font-weight: bold; font-size: 1.2em; margin-bottom:5px;\">[Internal Note] Tyler Santos<\/p>\n<p style=\"font-size: .9em; margin-top: 0px;\">Feb 09 2024, 03:07PM via System<\/p>\n<div class=\"s-la-preview-reply-body\">\n    <p>They said their email might not work, as they just made an ASURITE. Other email is:\u00a0jrosenthal@asuprep.org<\/p>\n<\/div>\n\n\n\n        <hr style=\"margin-top: 20px;\" \/>\n\n<p style=\"font-weight: bold; font-size: 1.2em; margin-bottom:5px;\">\n    Original Question<\/p>\n<p style=\"font-size: .9em; margin-top: 0px;\">Feb 09 2024, 02:56PM via Email<\/p>\n<div>\n    3D print request <br\/><p>Submitted on Fri, 02\/09\/2024 - 2:56 PM<\/p>\n  <b>Have you printed with us before?<\/b><br \/>Yes<br \/><br \/><b>First and last name<\/b><br \/>joseph rosenthal<br \/><br \/><b>ASU email address<\/b><br \/><a href=\"mailto:jrosen23@asu.edu\">jrosen23@asu.edu<\/a><br \/><br \/><b>ASU affiliation<\/b><br \/>asuprep digital<br \/><br \/><b>Is this print for a course or class project?<\/b><br \/>No<br \/><br \/><b>Which 3D printer was your model sliced for?<\/b><br \/>Creality Mill<br \/><br \/><b>Have you consulted with the Makerspace for this printer?<\/b><br \/>Yes<br \/><br \/><b>Estimated print weight (grams)<\/b><br \/>252<br \/><br \/><b>Filament color<\/b><br \/>I will provide my own filament<br \/><br \/><b>What color will you be using?<\/b><br \/>CDM<br \/><br \/><b>Upload your project<\/b><br \/><div>\n<span class=\"file file--mime-application-octet-stream file--general\"> <a href=\"https:\/\/lib.asu.edu\/system\/files\/webform\/3d_print_request\/21911\/cbelt45_04_pla_disc-2%289-%281.gcode\">cbelt45_04_pla_disc-2(9-(1.gcode<\/a><\/span>\n<\/div>\n<br \/><br \/>\n    <\/div>\n<br\/>\n\n\n\n<p style=\"font-weight: bold;\">\n    Questioner Information:\n<\/p>\n<p>\n    <strong>Name:<\/strong> joseph rosenthal<br\/>\n            <strong>Contact:<\/strong> jrosen23@asu.edu<br\/>\n        <\/p>\n\n\n<hr\/>\n<p>\n    <strong>Preview URL:<\/strong> <a href=\"https:\/\/askalibrarian.asu.edu\/admin\/ticket?qid=13171627&ticketclaim=0\" target=\"_blank\">https:\/\/askalibrarian.asu.edu\/admin\/ticket?qid=13171627&ticketclaim=0<\/a>\n<\/p>\n\n    <hr\/>\n        \n    <div>\n                <a href=\"https:\/\/askalibrarian.asu.edu\/admin\/ticket?qid=13171627&ticketclaim=0\"  class=\"btn btn-default\">\n            Preview        <\/a>\n        <button class=\"btn btn-default mg-left\" type=\"button\" data-dismiss=\"modal\">\n            Close        <\/button>\n    <\/div>\n    <script>\n    document.getElementById('removeTicketAssociation')?.addEventListener('submit', (ev) => {\n        ev.preventDefault();\n        const form = ev.target;\n        jQuery.ajax({\n            url: form.action,\n            method: form.method,\n            data: {},\n            dataType: 'json'\n        }).done(() => {\n            closeModal();\n            successAlert();\n            window.location.reload();\n        })\n        .fail(jqAjaxFailCallback);\n    });\n<\/script>\n"}"""

model_name = """cbelt45_04_pla_disc-2(9-(1.gcode"""
model_name = model_name.replace(" ",  "%20")
model_name = model_name.replace("<",  "%3C")
model_name = model_name.replace(">",  "%2E")
model_name = model_name.replace("#",  "%23")
model_name = model_name.replace("%",  "%25")
model_name = model_name.replace("+",  "%2B")
model_name = model_name.replace("{",  "%7B")
model_name = model_name.replace("}",  "%7D")
model_name = model_name.replace("|",  "%7C")
model_name = model_name.replace("\\", "%5C")
model_name = model_name.replace("^",  "%5E")
model_name = model_name.replace("~",  "%7E")
model_name = model_name.replace("[",  "%5B")
model_name = model_name.replace("]",  "%5D")
model_name = model_name.replace("`",  "%60")
model_name = model_name.replace(";",  "%3B")
model_name = model_name.replace("/",  "%2F")
model_name = model_name.replace("?",  "%3F")
model_name = model_name.replace(":",  "%3A")
model_name = model_name.replace("@",  "%40")
model_name = model_name.replace("=",  "%3D")
model_name = model_name.replace("&",  "%26")
model_name = model_name.replace("$",  "%24")
model_name = model_name.replace("(",  "%28")
model_name = model_name.replace(")",  "%29")

print(model_name)
x = re.search(f'[0-9][0-9][0-9][0-9][0-9]\\\\/{self.model_name}', modal_text)

print(x.group())