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
from bpy.props import *

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
    s = re.sub(r"\.|_|\(|\)|=|'|\"", "", name)
    return s.lower()

def toOperatorName(name):
    return "dskjal."+toClassName(name)

def toDeleteOperatorName(name):
    return toOperatorName(name)+'delete'

def toOperatorCommand(name):
    return toDeleteOperatorName(name)+'_'+toOperatorName(name)

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
    #
    def execute(self, context):
        context.scene.dskjal_generated_code = re.sub(r"\\"%s\\".+\\"%s\\"", "", context.scene.dskjal_generated_code, flags=re.DOTALL)
        remove = ('%s','%s')
        context.scene.dskjal_registerd_ops = context.scene.dskjal_registerd_ops.replace('%s','')
        context.scene.dskjal_registerd_ops = re.sub(r"(,$)|(^,)", "", context.scene.dskjal_registerd_ops)
        context.scene.dskjal_registerd_ops = context.scene.dskjal_registerd_ops.replace(',,',',')
        return{'FINISHED'}
"%s"
''' % (name, toClassName(name), toOperatorName(name), label, operation,
       toClassName(name), toOperatorName(name), name,
       name, name, toOperatorName(name), toDeleteOperatorName(name), toOperatorCommand(name), name)


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
        row.operator("dskjal.restorebutton")
        l.separator()
        l.prop(context.scene, 'dskjal_input_string')
        l.prop(context.scene, 'dskjal_button_name')
        l.operator("dskjal.registerbutton")

        if len(context.scene.dskjal_registerd_ops) == 0:
            return

        l.separator()
        tuples = context.scene.dskjal_registerd_ops.split(',')
        for t in tuples:
            names = t.split('_')
            row = l.row()
            row.operator(names[0], icon='PANEL_CLOSE', text='')
            row.operator(names[1])

class DskjalRegisterButton(bpy.types.Operator):
    bl_idname = "dskjal.registerbutton"
    bl_label = "Register operation"
  
    def execute(self, context):
        op = context.scene.dskjal_input_string
        if len(op) == 0:
            return{'FINISHED'}

        button_name = context.scene.dskjal_button_name
        if len(button_name) == 0:
            button_name = toClassName(op)
        oldcode = context.scene.dskjal_generated_code[:]
        context.scene.dskjal_generated_code += generate_button(toClassName(op) , button_name, op)
        try:
            exec(context.scene.dskjal_generated_code)
            bpy.utils.register_module(__name__)
        except:
            context.scene.dskjal_generated_code = oldcode
            return{'FINISHED'}

        if len(context.scene.dskjal_registerd_ops) == 0:
            context.scene.dskjal_registerd_ops += toOperatorCommand(op)
        else:
            context.scene.dskjal_registerd_ops += ',' + toOperatorCommand(op)

        context.scene.dskjal_input_string=''
        context.scene.dskjal_button_name =''

        return{'FINISHED'}

class DskjalRestoreButton(bpy.types.Operator):
    bl_idname = "dskjal.restorebutton"
    bl_label = "Restore operations"
  
    def execute(self, context):
        if len(context.scene.dskjal_generated_code) > 0:
            exec(context.scene.dskjal_generated_code)
            bpy.utils.register_module(__name__)
        return{'FINISHED'}

class DskjalClearCache(bpy.types.Operator):
    bl_idname = "dskjal.clearcachebutton"
    bl_label = "CLEAR ALL"
  
    def execute(self, context):
        context.scene.dskjal_generated_code = ''
        context.scene.dskjal_registerd_ops = ''
        return{'FINISHED'}

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
