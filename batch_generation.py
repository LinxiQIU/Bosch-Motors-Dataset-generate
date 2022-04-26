import blenderproc as bproc
import bpy
import os
import math
import random
import csv
import numpy as np
import h5py
import json
from PIL import Image, ImageFont, ImageDraw
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap




def import_MotorPart(Motor_path):
    need_items = []
    item_lst = os.listdir(Motor_path)
    for item in item_lst:
        fileName, fileExtension = os.path.splitext(item)
        if fileExtension == '.obj' and fileName != 'Motor':
            need_items.append(item)

    Motor_objs = []
    for i in need_items:
        obj_path = os.path.join(Motor_path, str(i))
        current_obj = bproc.loader.load_obj(obj_path)
        Motor_objs.extend(current_obj)

    for obj in Motor_objs:
        if 'Cover' in obj.get_name():
            obj.set_cp('category_id', 1)
        if 'Gear_Container' in obj.get_name():
            obj.set_cp('category_id', 2)
        if 'Inner_Gear' in obj.get_name():
            obj.set_cp('category_id', 3)
        if 'Charger' in obj.get_name():
            obj.set_cp('category_id', 4)
        if 'Bottom' in obj.get_name():
            obj.set_cp('category_id', 5)
        if 'Bolt' in obj.get_name():
            obj.set_cp('category_id', 6)

    return Motor_objs
        


def import_ClampingSystem(Clamping_path):
    Clamping_objs = bproc.loader.load_blend(Clamping_path)

    for obj in Clamping_objs:
        if 'Clamping' in obj.get_name():
            obj.set_cp('category_id', 7)
            obj.set_name('0000_ClampingSystem')
        if 'Plane' in obj.get_name():
            obj.set_cp('category_id', 8)
            obj.set_name('0000_Plane')
    
    return Clamping_objs


def init_lamp():

    light1 = bproc.types.Light()
    light1.set_type('POINT')
    light1.set_location([-2.1, -1.6, 4.8])
    light1.set_energy(random.randrange(500, 700, 50))

    light2 = bproc.types.Light()
    light2.set_type("POINT")
    light2.set_location([-1.7, 1.5, 4.2])
    light2.set_energy(random.randrange(500, 800, 50))

    light3 = bproc.types.Light()
    light3.set_type("POINT")
    light3.set_location([1.26, 0, 3])
    light3.set_energy(400)



def create_csv(csv_path):
    if not os.path.exists(csv_path):
        os.makedirs(csv_path)
    csv_path = csv_path + '/camera_motor_setting.csv'
    with open(csv_path, 'a+', newline = '') as f:
        csv_writer = csv.writer(f)
        head = ["positionX_camera", "positionY_camera", "positionZ_camera", "eulerX_camera", "eulerY_camera", "eulerZ_camera", "eulerX_motor", "eulerY_motor", "eulerZ_motor"]
        csv_writer.writerow(head)



def read_bottomLength(csv_path):
    bottomLength = []
    with open(csv_path,"r+") as f:
        csv_read = csv.reader(f)
        for line in csv_read:
            if line[8] != 'mf_Bottom_Length':
                bottomLength.append(float(line[8])*0.05)
    return bottomLength



def read_subBottomLength(csv_path):
    subBottomLength = []
    with open(csv_path,"r+") as f:
        csv_read = csv.reader(f)
        for line in csv_read:
            if line[9] != 'mf_Sub_Bottom_Length':
                subBottomLength.append(float(line[9])*0.05)
    return subBottomLength


def random_CameraPosition(radius_camera):
    r = radius_camera
    theta = [0, 20.0*math.pi/180.0]
    phi = [0, 2*math.pi]

    phi_camera = random.uniform(phi[0], phi[1])
    theta_camera = random.uniform(theta[0], theta[1])
    x_camera = r*math.cos(phi_camera)*math.sin(theta_camera) 
    y_camera = r*math.sin(phi_camera)*math.sin(theta_camera)
    z_camera = r*math.cos(theta_camera) 
    # bpy.data.objects['Camera'].location = (x_camera, y_camera, z_camera)
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects['Camera'].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Camera']
    beta1 = math.atan2(abs(y_camera), abs(z_camera))
    beta2 = math.asin(abs(x_camera) / (y_camera**2 + z_camera**2)**0.5)
    # rotation_z = -math.pi/2
    z = [-65*math.pi/180.0, -115*math.pi/180.0]
    rotation_z = random.uniform(z[0], z[1])
    
    if 0 < phi_camera < math.pi/2.0 :
        rotation_x = -beta2
        rotation_y = -beta1
    if math.pi/2.0 < phi_camera < math.pi :
        rotation_x = beta2
        rotation_y = -beta1
    if math.pi < phi_camera < 3.0*math.pi/2.0 :
        rotation_x = beta2
        rotation_y = beta1
    if 3.0*math.pi/2.0 < phi_camera < 2.0*math.pi :  
        rotation_x = -beta2
        rotation_y = beta1
    
    if phi_camera == 0.0 :
        rotation_x = theta_camera
        rotation_y = 0
    if phi_camera == math.pi/2.0 :
        rotation_x = 0
        rotation_y = theta_camera
    if phi_camera == math.pi :
        rotation_x = -theta_camera
        rotation_y = 0
    if phi_camera == 3.0*math.pi/2.0 :
        rotation_x = 0
        rotation_y = -theta_camera
    
    # bpy.data.objects['Camera'].rotation_euler = (rotation_x, rotation_y, rotation_z)
    euler_rotation = [rotation_x, rotation_y, rotation_z]
    bpy.ops.object.select_all(action='DESELECT')
    x_camera -= 0.915
    y_camera += 0.3 
    z_camera += 1.16
    # bpy.data.objects['Camera'].location = (x_camera, y_camera, z_camera)
    position = [x_camera, y_camera, z_camera]

    matrix_world = bproc.math.build_transformation_mat(position, euler_rotation)
    Cam_Info = [x_camera, y_camera, z_camera, rotation_x, rotation_y, rotation_z]

    return Cam_Info, matrix_world



def init_motor_position(Motor_type, Bottom_length, euler_motor):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if ('0000' not in obj.name) and ('Camera' not in obj.name):
            obj.select_set(True)
            obj.location = (0, 0, 0)
    ov = bpy.context.copy()
    ov['area'] = [a for a in bpy.context.screen.areas if a.type=="VIEW_3D"][0]
    bpy.ops.transform.rotate(ov, value=1.5708, orient_axis='Y', constraint_axis=(False, True, False),               
                    orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
    bpy.ops.transform.rotate(ov, value=-1.5708, orient_axis='X', constraint_axis=(True, False, False),               
                    orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
    bpy.ops.transform.rotate(ov, value=3.14159, orient_axis='Z', constraint_axis=(False, False, True), 
                    orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)                       
        
    if 'TypeB' in Motor_type:
        bpy.ops.transform.rotate(ov, value=1.5708+euler_motor[0], orient_axis='X', constraint_axis=(True, False, False), 
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.rotate(ov, value=euler_motor[1], orient_axis='Y', constraint_axis=(False, True, False),               
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.rotate(ov, value=euler_motor[2], orient_axis='Z', constraint_axis=(False, False, True), 
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.translate(value=(-0.02, 0, 0), constraint_axis=(False, False, False),
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
    if 'TypeA2' in Motor_type:
        bpy.ops.transform.rotate(ov, value=1.5708+euler_motor[0], orient_axis='X', constraint_axis=(True, False, False), 
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.rotate(ov, value=euler_motor[1], orient_axis='Y', constraint_axis=(False, True, False),               
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.rotate(ov, value=euler_motor[2], orient_axis='Z', constraint_axis=(False, False, True), 
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.translate(value=(0, 0,-0.03), constraint_axis=(False, False, False),
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
    if 'TypeA2' not in Motor_type and 'TypeA' in Motor_type:
        bpy.ops.transform.rotate(ov, value=euler_motor[0], orient_axis='X', constraint_axis=(True, False, False), 
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.rotate(ov, value=euler_motor[1], orient_axis='Y', constraint_axis=(False, True, False),               
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.rotate(ov, value=euler_motor[2], orient_axis='Z', constraint_axis=(False, False, True), 
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.translate(value=(0, 0,-0.02), constraint_axis=(False, False, False),
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
    bpy.ops.transform.translate(value=(-0.875+Bottom_length, 0.2, 1.14), constraint_axis=(False, False, False),
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
    


def init_whole_motor(Motor_type, Bottom_length, euler_motor):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if ('0000' not in obj.name) and ('Camera' not in obj.name) and ('Bolt' not in obj.name):
            obj.select_set(True)
            obj.location = (0, 0, 0)
    ov = bpy.context.copy()
    ov['area'] = [a for a in bpy.context.screen.areas if a.type=="VIEW_3D"][0]
    
    bpy.ops.transform.rotate(ov, value=1.5708, orient_axis='Y', constraint_axis=(False, True, False),               
                    orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
    bpy.ops.transform.rotate(ov, value=-1.5708, orient_axis='X', constraint_axis=(True, False, False),               
                    orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
    bpy.ops.transform.rotate(ov, value=3.14159, orient_axis='Z', constraint_axis=(False, False, True), 
                    orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)                       
        
    if 'TypeB' in Motor_type:
        bpy.ops.transform.rotate(ov, value=1.5708+euler_motor[0], orient_axis='X', constraint_axis=(True, False, False), 
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.rotate(ov, value=euler_motor[1], orient_axis='Y', constraint_axis=(False, True, False),               
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.rotate(ov, value=euler_motor[2], orient_axis='Z', constraint_axis=(False, False, True), 
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.translate(value=(-0.02, 0,0), constraint_axis=(False, False, False),
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
    if 'TypeA2' in Motor_type:
        bpy.ops.transform.rotate(ov, value=1.5708+euler_motor[0], orient_axis='X', constraint_axis=(True, False, False), 
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.rotate(ov, value=euler_motor[1], orient_axis='Y', constraint_axis=(False, True, False),               
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.rotate(ov, value=euler_motor[2], orient_axis='Z', constraint_axis=(False, False, True), 
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.translate(value=(0, 0,-0.03), constraint_axis=(False, False, False),
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
    if 'TypeA2' not in Motor_type and 'TypeA' in Motor_type:
        bpy.ops.transform.rotate(ov, value=euler_motor[0], orient_axis='X', constraint_axis=(True, False, False), 
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.rotate(ov, value=euler_motor[1], orient_axis='Y', constraint_axis=(False, True, False),               
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.rotate(ov, value=euler_motor[2], orient_axis='Z', constraint_axis=(False, False, True), 
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.translate(value=(0, 0,-0.02), constraint_axis=(False, False, False),
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
    bpy.ops.transform.translate(value=(-0.875+Bottom_length, 0.2, 1.14), constraint_axis=(False, False, False),
                        orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)


def read_hdf(output_folder):

    f = h5py.File(os.path.join(output_folder, '0.hdf5'), 'r')
    data1 = f['class_segmaps']
    data1 = np.asarray(data1)
    segcmap = ListedColormap(["darkgreen", "lime", "lavender", "yellow", "orange", "red", "navy", "lightblue"])
    plt.imsave(os.path.join(output_folder, 'class_segmaps.png'), data1, cmap=segcmap)

    data2 = f['colors']
    plt.imsave(os.path.join(output_folder, 'colors.png'), data2)

    data3 = f['distance']
    plt.imsave(os.path.join(output_folder, 'distance.png'), data3, cmap='plasma')

    data4 = f['normals']
    plt.imsave(os.path.join(output_folder, 'normals.png'), data4)



def delete_all():
    keep = ['Camera']
    for obj in bpy.data.objects:
        if not obj.name in keep:
            bpy.data.objects.remove(obj)



def save_coco(coco_path):
    with open(os.path.join(coco_path, 'coco_annotations.json')) as f:
        annotations = json.load(f)
        categories = annotations['categories']
        images = annotations['images']
        annotations = annotations['annotations']

    im = Image.open(os.path.join(coco_path, images[0]['file_name']))

    def get_category(_id):
        category = [category["name"] for category in categories if category["id"] == _id]
        return str(category[0])

    def rle_to_binary_mask(rle):
        binary_array = np.zeros(np.prod(rle.get('size')), dtype=np.bool)
        counts = rle.get('counts')

        start = 0
        for i in range(len(counts)-1):
            start += counts[i]
            end = start + counts[i+1]
            binary_array[start:end] = (i + 1) % 2

        binary_mask = binary_array.reshape(*rle.get('size'), order='F')

        return binary_mask

    font = ImageFont.load_default()
    # Add bounding boxes and masks
    for idx, annotation in enumerate(annotations):
        if annotation["image_id"] == 0:
            draw = ImageDraw.Draw(im)
            bb = annotation['bbox']
            draw.rectangle(((bb[0], bb[1]), (bb[0] + bb[2], bb[1] + bb[3])), fill=None, outline="red")
            draw.text((bb[0] + 2, bb[1] + 2), get_category(annotation["category_id"]), font=font)
            if isinstance(annotation["segmentation"], dict):
                im.putalpha(255)
                rle_seg = annotation["segmentation"]
                item = rle_to_binary_mask(rle_seg).astype(np.uint8) * 255
                item = Image.fromarray(item, mode='L')
                overlay = Image.new('RGBA', im.size)
                draw_ov = ImageDraw.Draw(overlay)
                rand_color = np.random.randint(0,256,3)
                draw_ov.bitmap((0, 0), item, fill=(rand_color[0], rand_color[1], rand_color[2], 128))
                im = Image.alpha_composite(im, overlay)
            else:
                # go through all polygons and plot them
                for item in annotation['segmentation']:
                    poly = Image.new('RGBA', im.size)
                    draw = ImageDraw.Draw(poly)
                    rand_color = np.random.randint(0,256,3)
                    pdraw.polygon(item, fill=(rand_color[0], rand_color[1], rand_color[2], 127), outline=(255, 255, 255, 255))
                    im.paste(poly, mask=poly)
    
    im.save(os.path.join(output_folder, 'coco_annotated_0.png'), "PNG")
    # im.show()




def main(num):
    
    Motor_file = '/home/linxi/KIT/Thesis/Dataset/motor_mesh_model/TypeB1'
    root, Motor_type = os.path.split(Motor_file)
    Clamping_path = '/home/linxi/KIT/Thesis/ClampingSystem/Scene_V1.blend'
    output_folder = '/home/linxi/KIT/Thesis/Training/' + Motor_type
    List_motor = os.listdir(Motor_file)
    if 'data.csv' in List_motor:
        List_motor.remove('data.csv')
    List_motor.sort()
    p = 3.1416/180
    BottomLength_all = read_bottomLength(Motor_file + '/data.csv')
    # sub_BottomLength_all = read_subBottomLength(Motor_file + '/data.csv')
    create_csv(output_folder)
    bproc.init()
    bproc.renderer.enable_distance_output(activate_antialiasing=False)
    flag=1
    for dirs in List_motor:
        # Clear all objects in the scene expect the camera
        delete_all()
        # Clear all key frames from the previous run
        bproc.utility.reset_keyframes()
        if flag > int(num):
            break
        try:
            delete_all()
        except KeyError:
            pass 
        k = dirs.split('_')       
        Bottom_length = BottomLength_all[int(k[1])-1]
        Clamping_objs = import_ClampingSystem(Clamping_path)
        Motor_path = os.path.join(Motor_file, dirs)
        # sub_BottomLength
        Motor_objs = import_MotorPart(Motor_path)
        for obj in Motor_objs:
            obj.set_scale([0.05, 0.05, 0.05])   
        euler_motor = np.random.uniform([-15*p, -5*p, -5*p], [15*p, 5*p, 5*p])
        init_motor_position(Motor_type, Bottom_length, euler_motor)
        cam_info, matrix_world = random_CameraPosition(radius_camera = random.uniform(2.8, 3.2))
        init_lamp()
        bproc.camera.add_camera_pose(matrix_world)
        bproc.camera.set_resolution(1280, 960)
        bproc.renderer.set_noise_threshold(0.05)
        bproc.renderer.enable_normals_output()
        data = bproc.renderer.render()
        data.update(bproc.renderer.render_segmap(map_by=["class"]))
        bproc.writer.write_hdf5(output_folder+'/Motor_'+str(k[1]), data)
        for obj in Motor_objs:
            if 'Bolt' not in obj.get_name():
                obj.delete()       
        for obj in Clamping_objs:
            obj.set_cp('category_id', 0)

        whole_motor = bproc.loader.load_obj(os.path.join(Motor_path, 'Motor.obj'))
        for obj in whole_motor:
            obj.set_cp('category_id', 10)
            obj.set_scale([0.05, 0.05, 0.05])
        init_whole_motor(Motor_type, Bottom_length, euler_motor)
        seg_data = bproc.renderer.render_segmap(map_by=["class", "instance", "name"])
        bproc.writer.write_coco_annotations(os.path.join(output_folder+'/Motor_'+str(k[1]), 'coco_data'),
                                instance_segmaps=seg_data["instance_segmaps"],
                                instance_attribute_maps=seg_data["instance_attribute_maps"],
                                colors=data["colors"],
                                color_file_format="JPEG")
        read_hdf(output_folder+'/Motor_'+str(k[1]))
        random_info = cam_info
        random_info.extend(euler_motor)
        random_info = ['{:.6f}'.format(i) for i in random_info]
        csv_path = output_folder + '/camera_motor_setting.csv'
        with open(csv_path, 'a+', newline='') as f:
            csv_writer = csv.writer(f)
            random_info = list(map(str, random_info))
            csv_writer.writerow(random_info)
        flag += 1
        




if __name__ == '__main__':
    models_num = 5
    main(num=models_num)







    
