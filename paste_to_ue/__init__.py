bl_info = {
    "name": "paste_to_ue",
    "author": "joric",
    "version": (0, 1),
    "blender": (2, 8, 0),
    "category": "Object",
    "location": "View 3D > Object",
    "description": "Copy transformations of objects to paste to UE",
    "doc_url": "https://github.com/joric/paste_to_ue",
}

addon_keymaps = []

import bpy
from math import*

class MeshSeparation(bpy.types.Operator):
    bl_idname = "object.debug_macro_paste_to_ue"
    bl_label = "Debug Macro 2"
    bl_options = {'REGISTER', 'UNDO'}

    delta: bpy.props.StringProperty(name="delta", default="0.1")

    # WIP: mesh separation for 
    def execute(self, context: bpy.context):
        import sys,imp

        module = sys.modules['paste_to_ue']
        imp.reload(module)

        objects = []

        #transform values for every selected object
        for o in bpy.context.selected_objects:
            if o.type != "MESH":
                continue
            points = []
            bpy.context.view_layer.objects.active = o
            active = bpy.context.object.name
            for v in o.data.vertices:
                points.append(v.co)
            objects.append(points)

        #self.report({'INFO'}, f'Collected points {[len(p) for p in objects]}')

        if len(objects)<2 or len(objects[0])<3 or len(objects[1])<3:
            self.report({'INFO'}, f'Too few objects selected, need two (template and cloud) with 3 points each, minimum.')
            return {'FINISHED'}

        template, cloud = sorted(objects,key=len)[:2]
        n,m = map(len,(template,cloud))

        self.report({'INFO'}, f'Collected points template:{n}, cloud: {m} ({m/n})')

        # calculate distances from first point to other points, sort distances
        print(template, cloud[:n])

        ofs = 0
        while ofs+n <= m:
            loc = cloud[ofs]
            #bpy.ops.object.empty_add(location=loc)
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
