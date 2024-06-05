bl_info = {
    "name": "paste_to_ue",
    "author": "joric",
    "version": (0, 1),
    "blender": (3, 6, 0),
    "category": "Object",
    "location": "View 3D > Object",
    "description": "Copy transformations of objects to paste to UE",
    "doc_url": "https://github.com/joric/paste_to_ue",
}

addon_keymaps = []

import bpy
from math import *
import mathutils
from mathutils import *

class MeshSeparation(bpy.types.Operator):
    bl_idname = "object.debug_macro_paste_to_ue"
    bl_label = "Debug Macro 2"
    bl_options = {'REGISTER', 'UNDO'}

    delta: bpy.props.StringProperty(name="delta", default="0.1")

    # WIP: mesh separation for template vs point cloud
    def execute(self, context: bpy.context):
        import sys,imp

        module = sys.modules['paste_to_ue']
        imp.reload(module)

        objects = []

        # collect points for every selected object
        for o in bpy.context.selected_objects:
            if o.type != "MESH":
                continue

            points = []
            bpy.context.view_layer.objects.active = o
            active = bpy.context.object.name

            #for v in o.data.vertices:
            #    points.append(v.co)

            # need to collect points from face data here, or it doesn't match
            for face in o.data.polygons:
                for idx in face.vertices:
                    points.append( o.data.vertices[idx].co )

            objects.append(points)

        if len(objects)<2 or len(objects[0])<3 or len(objects[1])<3:
            self.report({'INFO'}, f'Too few objects selected, need two (template and cloud) with 3 points each, minimum.')
            return {'FINISHED'}

        template, cloud = sorted(objects,key=len)[:2]
        n,m = map(len,(template,cloud))

        self.report({'INFO'}, f'Collected points template:{n}, cloud: {m}, ratio: ({m/n})')

        #print(template, cloud[:n])

        ofs = 0
        while ofs+n <= m:
            loc = cloud[ofs]

            source_points = template[:3]
            target_points = [cloud[ofs+i]-loc for i in range(3)]

            source_distance = (source_points[1] - source_points[0]).length
            target_distance = (target_points[1] - target_points[0]).length
            scaling_factor = target_distance / source_distance
            scale = ([scaling_factor]*3)

            source_vector = source_points[0].copy() # normalize messes up original if not copied
            target_vector = target_points[0].copy()

            source_vector.normalize()
            target_vector.normalize()

            rotation_quat = source_vector.rotation_difference(target_vector)
            #rotation_quat = target_vector.rotation_difference(source_vector)

            add_instance = True
            if add_instance:

                # does not rotate properly. do we need centroids?

                source_object = bpy.context.selected_objects[0 if len(objects[0])<len(objects[1]) else 1]
                instance_object = bpy.data.objects.new(name='InstanceObject', object_data=source_object.data)
                bpy.context.collection.objects.link(instance_object)

                instance_object.location = loc
                instance_object.rotation_quaternion = rotation_quat
                instance_object.scale = scale

                #instance_object.matrix_world = Matrix.Translation(loc) @ rotation_quat.to_matrix().to_4x4() @ Matrix.Scale(scaling_factor,4)

                bpy.context.view_layer.update()

            else:

                bpy.ops.object.empty_add(location = loc, rotation=rotation_quat.to_euler(), scale = scale)


            ofs += n

        #import json
        #data = {'template':[(v.x,v.y,v.z)for v in template],'cloud':[(v.x,v.y,v.z)for v in cloud]};
        #json.dump(data, open('c:/temp/out.json','w'), indent=2)

        return {'FINISHED'}


def copy_to_clipboard(self, blueprint, scale):

    actors = []

    #transform values for every selected object
    for o in bpy.context.selected_objects:
        #make the object active
        bpy.context.view_layer.objects.active = o

        #variable for getting the active object name
        active = bpy.context.object.name

        #check for quaternion rotation
        r = o.rotation_quaternion.to_euler() if o.rotation_mode=='QUATERNION' else o.rotation_euler
        l = o.location
        out = f'add("{blueprint}",{l.x*100,-l.y*100,l.z*100},{r.x,-r.y,-r.z})'

        if scale > 0:
            s = o.scale
            out += f'.set_actor_scale3d(unreal.Vector{s.x*scale,s.y*scale,s.z*scale})'

        actors.append(out)

    bpy.context.window_manager.clipboard = '''eli,eal=unreal.EditorLevelLibrary,unreal.EditorAssetLibrary
load=lambda bp:eal.load_blueprint_class(eal.load_asset(bp).get_outer().get_full_name())
add=lambda bp,v,r:eli.spawn_actor_from_class(load(bp),unreal.Vector(*v),unreal.Rotator(*r))
'''+ '\n'.join(actors)

    self.report({'INFO'}, f"{len(actors)} UE Object(s) Copied to Clipboard")

class PasteToUE(bpy.types.Operator):
    bl_idname = "object.paste_to_ue"
    bl_label = "Paste to UE"
    bl_options = {'REGISTER', 'UNDO'}

    blueprint: bpy.props.StringProperty(name="blueprint", default="/Game/Items/BP_Item")
    scale: bpy.props.FloatProperty(name="scale", default=0)

    def execute(self, context):
        copy_to_clipboard(self, self.blueprint, self.scale)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(PasteToUE.bl_idname)

def register():
    bpy.utils.register_class(PasteToUE)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    # handle the keymap
    wm = bpy.context.window_manager

    bpy.utils.register_class(MeshSeparation)

    if wm.keyconfigs.addon:
        km = wm.keyconfigs.addon.keymaps.new(name="Window", space_type='EMPTY')
        kmi = km.keymap_items.new(MeshSeparation.bl_idname, 'D', 'PRESS', ctrl=True, shift=True)
        kmi = km.keymap_items.new(PasteToUE.bl_idname, 'C', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_class(PasteToUE)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


    bpy.utils.unregister_class(MeshSeparation)

    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    del addon_keymaps[:]

if __name__ == "__main__":
    register()
