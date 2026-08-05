import bpy
from math import radians
from bpy.props import *

class MyOperator(bpy.types.Operator):
    bl_idname = "object.my_operator"
    bl_label = "My Operator"
    bl_options = {'REGISTER', 'UNDO'}

    # create properties
    noise_scale : FloatProperty(
        name = "Noise Scale",
        description = "The scale of the noise",
        default = 1.0,
        min = 0.0,
        max = 2.0
    )

    def execute(self, context):
 
        # create cube
        bpy.ops.mesh.primitive_cube_add()
        so = bpy.context.active_object

        # move object
        so.location[0] = 5

        # rotation object
        # degrees = 45
        # rad = degrees * pi/180
        #radians(45)

        so.rotation_euler[0] += radians(45)

        # create modifier
        mod_subsurf = so.modifiers.new("my modifier", 'SUBSURF')

        # change modifier value
        mod_subsurf.levels = 3

        # smooth the object
        bpy.ops.object.shade_smooth()

        # create displacement modifier
        mod_displace = so.modifiers.new("my displacement", 'DISPLACE')

        # create the texture
        new_tex = bpy.data.textures.new("my texture", 'DISTORTED_NOISE')

        # change the texture settings
        new_tex.noise_scale = self.noise_scale

        # assign the texture to displacement modifier
        mod_displace.texture = new_tex

        # create the material
        new_mat = bpy.data.materials.new(name = "my material")
        so.data.materials.append(new_mat)

        new_mat.use_nodes = True
        nodes = new_mat.node_tree.nodes

        material_output = nodes.get("Material Output")
        node_emission = nodes.new(type='ShaderNodeEmission')

        # color
        node_emission.inputs[0].default_value = (0.0, 0.3, 1.0, 1)

        # strength
        node_emission.inputs[1].default_value = 500.0

        links = new_mat.node_tree.links
        new_link = links.new(node_emission.outputs[0], material_output.inputs[0])
        
      
        
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(MyOperator.bl_idname, text=MyOperator.bl_label)


def register():
    bpy.utils.register_class(MyOperator)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(MyOperator)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    register()

    # Test call.
    bpy.ops.object.my_operator()
