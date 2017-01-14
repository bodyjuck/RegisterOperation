# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
import bpy
import re
import mathutils
import os.path
import uuid
from bpy.props import *
from bpy.app.handlers import persistent

bl_info = {
    "name": "register operation",
    "author": "dakjal",
    "version": (1, 0),
    "blender": (2, 78, 0),
    "location": "Tool Shelf > Tools",
    "description": "register any operation on Tool Shelf",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User"
}

#-----------------------------------helper function------------------------------------------
def toClassName(name):
    s = re.sub(r"\.|_|\(|\)|=|'|\"| |-|~|:|//|\^", "", name)
    return s.lower()

def toOperatorName(name):
    return "dskjal."+toClassName(name)

def toDeleteOperatorName(name):
    return toOperatorName(name)+'delete'

def toOperatorCommand(class_name, button_name):
    return toDeleteOperatorName(class_name)+'_'+toOperatorName(class_name)+'^'+button_name

def genRandomName(bottonNames):
    candidate = str(uuid.uuid4())
    while candidate in bottonNames:
        candidate = str(uuid.uuid4())
    return candidate
    
def generate_button(name, label, operation):
    return '''
"%s"
class Dskjal%sButton(bpy.types.Operator):
    bl_idname = "%s"
    bl_label = "%s"
  
    def execute(self, context):
        %s
        return{'FINISHED'}

class Dskjal%sDeleteButton(bpy.types.Operator):
    bl_idname = "%sdelete"
    bl_label = "%sdelete"
    
    def execute(self, context):
        context.scene.dskjal_generated_code = re.sub(r"\\"%s\\".+\\"%s\\"", "", context.scene.dskjal_generated_code, flags=re.DOTALL)
        remove = ('%s','%s')
        context.scene.dskjal_registerd_ops = context.scene.dskjal_registerd_ops.replace('%s','')
        context.scene.dskjal_registerd_ops = re.sub(r"(,$)|(^,)", "", context.scene.dskjal_registerd_ops)
        context.scene.dskjal_registerd_ops = context.scene.dskjal_registerd_ops.replace(',,',',')
        print(context.scene.dskjal_registerd_ops)
        return{'FINISHED'}
"%s"
''' % (toClassName(name), toClassName(name), toOperatorName(name), label, operation,
       toClassName(name), toOperatorName(name), label,
       toClassName(name), toClassName(name), toOperatorName(name), toDeleteOperatorName(name), toOperatorCommand(name, label), toClassName(name))


#----------------------------------------------------UI-----------------------------------------------------------
class DskjalRegisterOpUI(bpy.types.Panel):
    bl_label = "Operation Shelf"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Tools"

    bpy.types.Scene.dskjal_input_string = bpy.props.StringProperty(name='Operation', default='')
    bpy.types.Scene.dskjal_button_name = bpy.props.StringProperty(name='Name', default='')
    bpy.types.Scene.dskjal_generated_code = bpy.props.StringProperty(name='generated code')
    bpy.types.Scene.dskjal_registerd_ops = bpy.props.StringProperty(name='ops')

    def draw(self, context):
        l = self.layout.column()
        row = l.row()
        row.operator("dskjal.clearcachebutton", icon='PANEL_CLOSE', text='')
        row.label('CLEAR ALL')
        l.separator()
        l.prop(context.scene, 'dskjal_input_string')
        l.prop(context.scene, 'dskjal_button_name')
        l.operator("dskjal.registerbutton")

        if len(context.scene.dskjal_registerd_ops) == 0:
            return

        l.separator()
        tuples = context.scene.dskjal_registerd_ops.split(',')
        for t in tuples:
            button_ids = t.split('_')
            row = l.row()
            row.operator(button_ids[0], icon='PANEL_CLOSE', text='')
            
            b = button_ids[1].split('^')
            row.operator(b[0], text=b[1])

class DskjalRegisterButton(bpy.types.Operator):
    bl_idname = "dskjal.registerbutton"
    bl_label = "Register operation"
  
    def execute(self, context):
        op = context.scene.dskjal_input_string
        if len(op) == 0:
            return{'FINISHED'}

        if os.path.isfile(op):
            f = open(op)
            op = f.read()
            f.close()

            #add indent
            op = op.replace('\n','\n        ')
            

        button_name = context.scene.dskjal_button_name
        if len(button_name) == 0:
            return{'FINISHED'}

        oldcode = context.scene.dskjal_generated_code
        class_name = genRandomName(context.scene.dskjal_registerd_ops)
        context.scene.dskjal_generated_code += generate_button(class_name, button_name, op)
        try:
            exec(context.scene.dskjal_generated_code)
            bpy.utils.register_module(__name__)
        except:
            context.scene.dskjal_generated_code = oldcode
            print('exec or register failed')
            return{'FINISHED'}

        if len(context.scene.dskjal_registerd_ops) == 0:
            context.scene.dskjal_registerd_ops += toOperatorCommand(class_name, button_name)
        else:
            context.scene.dskjal_registerd_ops += ',' + toOperatorCommand(class_name, button_name)

        context.scene.dskjal_input_string=''
        context.scene.dskjal_button_name =''

        return{'FINISHED'}

class DskjalClearCache(bpy.types.Operator):
    bl_idname = "dskjal.clearcachebutton"
    bl_label = "CLEAR ALL"
  
    def execute(self, context):
        context.scene.dskjal_generated_code = ''
        context.scene.dskjal_registerd_ops = ''
        return{'FINISHED'}

@persistent
def load_handler(dummy):
    if len(bpy.context.scene.dskjal_generated_code) > 0:
        exec(bpy.context.scene.dskjal_generated_code)
        bpy.utils.register_module(__name__)

def register():
    bpy.utils.register_module(__name__)
    bpy.app.handlers.load_post.append(load_handler)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.app.handlers.load_post.remove(load_handler)

if __name__ == "__main__":
    register()
