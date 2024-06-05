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

    # mesh separation, template vs point cloud
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

        source_index = 0 if len(objects[0])<len(objects[1]) else 1
        template_obj = bpy.context.selected_objects[source_index]

        ofs = 0
        while ofs+n <= m:
            obj = bpy.data.objects.new(name=template_obj.name+'_instance', object_data=template_obj.data)
            #obj = bpy.data.objects.new(name=template_obj.name+'_empty', object_data = None)
            bpy.context.collection.objects.link(obj)

            source_points = template[:3]
            target_points = cloud[ofs:ofs+3]

            a,b,c = [[source_points[i],target_points[i]] for i in range(3)]
            p = obj.location.copy(), a[1]

            def calc_matrix(i):
                x = (b[i] - a[i]).normalized()
                z = x.cross(c[i] - a[i]).normalized()
                y = z.cross(x).normalized()
                w = p[i].copy()
                w.resize_4d()
                m = Matrix()
                m[0], m[1], m[2], m[3] = x.resized(4), y.resized(4), z.resized(4), w
                m.transpose()
                return m

            dest, src = calc_matrix(0), calc_matrix(1)
            r = src @ dest.inverted() @ obj.matrix_world.copy()

            scale = (b[1] - a[1]).length / (b[0] - a[0]).length
            r.transpose()
            for i in range(3):
                r[i].xyz *= scale
            r.transpose()

            snap = obj.matrix_world.inverted() @ a[0]
            obj.matrix_world = Matrix().Translation(r.to_translation() - r @ snap) @ r

            ofs += n

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
