import bpy
import math
import random
import time
from mathutils import Euler, Color
from pathlib import Path

def randomly_rotate_object(obj_to_change):
    '''Applies a random rotation to an object
    '''

    random_rot = (0, 0, random.random() * 2 * math.pi)
    obj_to_change.rotation_euler = Euler(random_rot, 'XYZ')

def randomly_change_color(material_to_change):
    '''Changes the Principled BSDF color of a material to a random color
    '''
    
    color = Color()
    hue = random.random() * .2 # random between 0 and .2
    saturation = random.random() * .6 + .2 # random between .2 and .8
    color.hsv = (hue, saturation, 1)
    rgba = [color.r, color.g, color.b, 1]
    material_to_change.node_tree.nodes["Principled BSDF"].inputs[0].default_value = rgba

def randomly_set_camera_position():
    # Set the circular path position (0 to 100)
    bpy.context.scene.objects['CameraContainer'].constraints['Follow Path'].offset = random.random() * 100

    # Set the arc path position (0 to -100, not sure why, to be honest)
    bpy.context.scene.objects['CirclePathContainer'].constraints['Follow Path'].offset = random.random() * -100

# Object names to render
cup_name = 'Glass_Mug'
cup_obj = bpy.context.scene.objects[cup_name]
tea_names = ['Full', 'Half-Full', 'Mostly-Empty', 'Empty']
obj_count = len(tea_names)

# Number of images to generate of each object for each split of the dataset
# Example: ('train', 100) means generate 100 images each of Full', 'Half-Full', 'Mostly-Empty', 'Empty' resulting in 400 training images
obj_renders_per_split = [('train', 3)]
#obj_renders_per_split = [('train', 500), ('val', 120)]

# Output path
output_path = Path('/Users/fefdiniz/Documents/Documentos-MacBookProdeFernanda/UnB/Fastcamp/FastCamp-Dados-Sinteticos/card09')

# For each dataset split (train/val/test), multiply the number of renders per object by
# the number of objects (3, since we have A, B, and C). Then compute the sum.
# This will be the total number of renders performed.
total_render_count = sum([obj_count * r[1] for r in obj_renders_per_split])

# Set all objects to be hidden in rendering
for name in tea_names:
    if name != 'Empty':
        bpy.context.scene.objects[name].hide_render = True

# Tracks the starting image index for each object loop
start_idx = 0

# Keep track of start time (in seconds)
start_time = time.time()

# Loop through each split of the dataset
for split_name, renders_per_object in obj_renders_per_split:
    print(f'Starting split: {split_name} | Total renders: {renders_per_object * obj_count}')
    print('=============================================')

    # Loop through the objects by name
    for obj_name in tea_names:
        print(f'Starting object: {split_name}/{obj_name}')
        print('.............................................')
        # Get the next object and make it visible
        if obj_name != 'Empty':
            obj_to_render = bpy.context.scene.objects[obj_name]
            obj_to_render.hide_render = False

        # Loop through all image renders for this object
        for i in range(start_idx, start_idx + renders_per_object):
            # Change the object
            randomly_rotate_object(cup_obj)
            randomly_set_camera_position()
            randomly_change_color(obj_to_render.material_slots[0].material)

            # Log status
            print(f'Rendering image {i + 1} of {total_render_count}')
            seconds_per_render = (time.time() - start_time) / (i + 1)
            seconds_remaining = seconds_per_render * (total_render_count - i - 1)
            print(f'Estimated time remaining: {time.strftime("%H:%M:%S", time.gmtime(seconds_remaining))}')

            # Update file path and render
            bpy.context.scene.render.filepath = str(output_path / split_name / obj_name / f'{str(i).zfill(6)}.png')
            bpy.ops.render.render(write_still=True)

        if obj_name != 'Empty':
            # Hide the object, we're done with it
            obj_to_render.hide_render = True

        # Update the starting image index
        start_idx += renders_per_object

# Set all objects to be visible in rendering
for name in tea_names:
    if name != 'Empty':
        bpy.context.scene.objects[name].hide_render = False