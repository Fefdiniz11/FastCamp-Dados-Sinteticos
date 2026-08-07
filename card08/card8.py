import bpy
import math
import random
import time
from mathutils import Euler, Color
from pathlib import Path

# random rotation to an object
def randomly_rotate_object(obj_to_change):
    random_rot = (random.random()*2*math.pi, random.random()*2*math.pi, random.random()*2*math.pi)
    obj_to_change.rotation_euler = Euler(random_rot, 'XYZ')
    
# changes the principled BSDF color of a material to a random color
def randomly_change_color(material_to_change):
    color = Color()
    # random hue between 0 and 1
    hue = random.random() 
    color.hsv = (hue, 1, 1)
    rgba = [color.r, color.g, color.b, 1]
    material_to_change.node_tree.nodes['Principled BSDF'].inputs[0].default_value = rgba
    
    
# object names to render
obj_names = ['A', 'B', 'C']
obj_count = len(obj_names)

# number of images to generate each object for each split od the dataset
# obj_renders_per_split = [('train', 3), ('val', 2), ('test', 1)]
obj_renders_per_split = [('train', 300), ('val', 80), ('test', 10)]

output_path = Path('/Users/fefdiniz/Documents/Documentos-MacBookProdeFernanda/UnB/Fastcamp/FastCamp-Dados-Sinteticos/card8/render')

# for each dataset split (train/val/test), multiply the number of renders per object by the number of objects
# then compute the sum
total_render_count = sum([obj_count * r[1] for r in obj_renders_per_split])

# set all objects to be hidden in rendering
for name in obj_names:
    bpy.context.scene.objects[name].hide_render = True
    
# tracks the starting image indez for each object loop
start_idx = 0

# keep track of start time (in seconds)
start_time = time.time()

# loop through each split of the dataset
for split_name, renders_per_object in  obj_renders_per_split: 
    print(f'Starting split: {split_name} | Total renders: {renders_per_object * obj_count}')
    print('============================')
    
    # loop through the object by name
    for obj_name in obj_names:
        print(f'Starting object: {split_name}/{obj_name}')
        print('.........................')
        
        # get the next object and make it visible
        obj_to_render = bpy.context.scene.objects[obj_name]
        obj_to_render.hide_render = False
        
        # loop through all image renders for this object
        for i in range (start_idx, start_idx + renders_per_object):
            # change the object
            randomly_rotate_object(obj_to_render)
            randomly_change_color(obj_to_render.material_slots[0].material)
            
            # log status
            print(f'Rendering image {i+1} of {total_render_count}')
            seconds_per_render = (time.time() - start_time) / (i+1)
            seconds_remaining = seconds_per_render * (total_render_count-i-1)
            print(f'Estimated time remaining: {time.strftime("%H:%M:%S", time.gmtime(seconds_remaining))}')
            
            # update file path and render
            bpy.context.scene.render.filepath = str(output_path / split_name / obj_name / f'{str(i).zfill(6)}.png')
            bpy.ops.render.render(write_still=True)
            
        
        # hide the object
        obj_to_render.hide_render = True
            
        # update the starting image index
        start_idx += renders_per_object
        
# set all object to be visible in rendering
for name in obj_names:
    bpy.context.scene.objects[name].hide_render = False