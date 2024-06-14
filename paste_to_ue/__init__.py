bl_info = {
    "name": "paste_to_ue",
    "author": "joric",
    "version": (0, 3),
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
from collections import *
import sys,imp

def align(template, cloud, ofs, obj, cloud_obj, scale=True):
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

    if scale:
        scale = (b[1] - a[1]).length / (b[0] - a[0]).length
        r.transpose()
        for i in range(3):
            r[i].xyz *= scale
        r.transpose()

    snap = obj.matrix_world.inverted() @ a[0]
    offset = r.to_translation() - r @ snap
    parent = cloud_obj.matrix_world

    obj.matrix_world = parent @ Matrix().Translation(offset) @ r

def get_points(o):
    points = []
    for face in o.data.polygons:
        for idx in face.vertices:
            points.append( o.data.vertices[idx].co )
    return points

def break_mesh():
    base_mesh = None
    for o in bpy.context.selected_objects:
        base_mesh = o
    if not base_mesh: return []
    # merge vertices with some tolerance value
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action = 'SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.01)
    # break mesh into separate objects
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')

    meshes = []
    for o in bpy.context.selected_objects:
        meshes.append(o)
    return meshes

def create_templates():
    # creates axis-aligned copies of unique objects
    templates = []
    meshes = []
    collection = {}
    for o in bpy.context.selected_objects:
        # group by number of points for now
        points = get_points(o)
        key = len(points)
        if key not in collection:
            collection[key] = o
        meshes.append(o)

    for template_obj in collection.values():
        # duplicate object with geometry
        obj = bpy.data.objects.new(name=template_obj.name+'_template', object_data=template_obj.data.copy())
        bpy.context.collection.objects.link(obj)

        # align object to axes and set origin to the bottom plane
        bpy.ops.object.select_all(action = 'DESELECT')
        obj.select_set(True)
        obj.matrix_world.identity()
        bpy.ops.object.origin_set()

        # let's align using existing tools
        cloud = [Vector((0,0,0)), Vector((0,1,0)), Vector((1,0,0))]
        template = get_points(obj)
        align(template, cloud, 0, obj, obj, False)

        # move origin to center of x,y plane, leave z intact
        obj.location = Vector((0,0, obj.location.z))

        # apply all transformations
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        templates.append(obj)

    # need to select both templates and input objects for future operations
    bpy.ops.object.select_all(action = 'DESELECT')
    for o in meshes:
        o.select_set(True)
    for o in templates:
        o.select_set(True)

    return templates

def make_instances():
    # input - selected objects
    # templates are either selected last or have 'template' in name

    templates = []
    last_object = None
    if not templates:
        for o in bpy.context.selected_objects:
            last_object = o
            if 'template' in o.name:
                templates.append(o)

    if not templates:
        templates.append(last_object)

    instances = []
    for template_obj in templates:
        template = get_points(template_obj)

        for o in bpy.context.selected_objects:
            if o == template_obj:
                continue

            cloud_obj = o
            cloud = get_points(cloud_obj)

            if len(cloud) != len(template):
                continue

            obj = bpy.data.objects.new(name=template_obj.name+'_instance', object_data=template_obj.data)
            bpy.context.collection.objects.link(obj)
            align(template, cloud, 0, obj, cloud_obj)
            instances.append(obj)
    return instances

class CustomTabPanel1(bpy.types.Panel):
    bl_label = "Match Templates"
    bl_idname = "MY_PT_CustomTabPanel1"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paste to UE'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "custom_delta")
        layout.prop(context.scene, "custom_radio_selection", expand=True)
        layout.operator("custom.button_operator1", text="Create Instances")

class CustomTabPanel2(bpy.types.Panel):
    bl_label = "Copy Transforms"
    bl_idname = "MY_PT_CustomTabPanel2"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paste to UE'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "path_to_blueprint")
        layout.prop(context.scene, "use_scale")
        layout.prop(context.scene, "custom_scale")
        layout.operator("custom.button_operator2", text="Copy to Clipboard")

class CustomTabPanel3(bpy.types.Panel):
    bl_label = "Auto Mesh Separation"
    bl_idname = "MY_PT_CustomTabPanel3"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paste to UE'

    def draw(self, context):
        layout = self.layout
        layout.operator("custom.button_operator3", text="Auto Mesh Separation")

class CustomTabPanel4(bpy.types.Panel):
    bl_label = "Step by Step"
    bl_idname = "MY_PT_CustomTabPanel4"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paste to UE'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator("custom.button_operator4", text="Break Mesh")
        layout.operator("custom.button_operator5", text="Create Templates")
        #layout.operator("custom.button_operator6", text="Create Instances")
        layout.operator("custom.button_operator7", text="Make Instances")

# Auto Mesh Separation
class CustomButtonOperator3(bpy.types.Operator):
    bl_idname = "custom.button_operator3"
    bl_label = "Custom Button"

    def execute(self, context):

        meshes = break_mesh()
        templates = create_templates()
        instances = make_instances()

        # cleanup
        bpy.ops.object.select_all(action = 'DESELECT')
        for o in meshes:
            o.select_set(True)
        bpy.ops.object.delete()

        self.report({'INFO'}, f'finished, found {len(templates)} templates, created {len(instances)} instances.')
        return {'FINISHED'}

# Match Templates
class CustomButtonOperator1(bpy.types.Operator):
    bl_idname = "custom.button_operator1"
    bl_label = "Custom Button"

    def execute(self, context):
        import sys,imp

        delta = context.scene.custom_delta
        create_instances = context.scene.custom_radio_selection == 'INSTANCES'

        objects = []
        meshes = []

        # collect points for every selected object
        for o in bpy.context.selected_objects:
            if o.type != 'MESH':
                continue

            meshes.append(o)
            points = []
            bpy.context.view_layer.objects.active = o

            # need to collect points from face data, or it doesn't match
            for face in o.data.polygons:
                for idx in face.vertices:
                    points.append( o.data.vertices[idx].co )

            objects.append(points)

        indices = list(range(len(objects)))
        indices.sort(key = lambda i:len(objects[i]))
        objects.sort(key=len)

        if len(objects)<2 or len(objects[0])<3 or len(objects[1])<3:
            self.report({'INFO'}, f'Too few objects selected, need two (template and cloud) with 3 points each, minimum.')
            return {'FINISHED'}

        templates, cloud = objects[:-1], objects[-1]

        # calculate distance from first to last point of the object
        # then calculate distance from first to the middle point
        # calculate weighted dist = half_dist / full_dist
        # check if cloud dist match template dist within given delta
        def match(template, cloud, ofs, delta):
            n,m = map(len,(template,cloud))
            if ofs+n > m:
                return False
            def calc_dist(points, ofs, n):
                full_dist = (points[ofs]-points[ofs + n-1]).length
                half_dist = (points[ofs]-points[ofs + n//2]).length
                return half_dist / full_dist if full_dist else 0
            return abs(calc_dist(template, 0, n) - calc_dist(cloud, ofs, n)) < delta

        m = len(cloud)
        self.report({'INFO'}, f'Collected cloud points {m}, matching against {len(templates)} templates...')

        ofs = count = 0
        while ofs < m:
            n = 1
            for i,template in enumerate(templates):

                if match(template, cloud, ofs, delta):
                    template_obj, cloud_obj = meshes[indices[i]], meshes[indices[-1]]

                    if create_instances:
                        obj = bpy.data.objects.new(name=template_obj.name+'_instance', object_data=template_obj.data)
                    else:
                        obj = bpy.data.objects.new(name=template_obj.name+'_empty', object_data = None)
                    bpy.context.collection.objects.link(obj)

                    align(template, cloud, ofs, obj, cloud_obj)
                    n = len(template)
                    count += 1

            ofs += n

        self.report({'INFO'}, f'Matching finished, created {count} instances.')
        return {'FINISHED'}

# Paste to Clipboard
class CustomButtonOperator2(bpy.types.Operator):
    bl_idname = "custom.button_operator2"
    bl_label = "Custom Button 2"

    def execute(self, context):
        copy_to_clipboard(self, context.scene.path_to_blueprint, context.scene.custom_scale if context.scene.use_scale else 0)
        self.report({'INFO'}, "Copied to clipboard.")
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
        out = f'add("{blueprint}",{l.x*100,-l.y*100,l.z*100},{degrees(r.x),degrees(-r.y),degrees(-r.z)})'

        if scale > 0:
            s = o.scale
            out += f'.set_actor_scale3d(unreal.Vector{s.x*scale,s.y*scale,s.z*scale})'

        actors.append(out)

    bpy.context.window_manager.clipboard = '''eli,eal=unreal.EditorLevelLibrary,unreal.EditorAssetLibrary
load=lambda bp:eal.load_blueprint_class(eal.load_asset(bp).get_outer().get_full_name())
add=lambda bp,v,r:eli.spawn_actor_from_class(load(bp),unreal.Vector(*v),unreal.Rotator(*r))
'''+ '\n'.join(actors)

    self.report({'INFO'}, f"{len(actors)} UE Object(s) Copied to Clipboard")

# Break Mesh
class CustomButtonOperator4(bpy.types.Operator):
    bl_idname = "custom.button_operator4"
    bl_label = "Custom Button 4"

    def execute(self, context):
        break_mesh()
        return {'FINISHED'}

# Create Templates
class CustomButtonOperator5(bpy.types.Operator):
    bl_idname = "custom.button_operator5"
    bl_label = "Custom Button 5"
    def execute(self, context):
        create_templates()
        return {'FINISHED'}

# Build Templates
class CustomButtonOperator6(bpy.types.Operator):
    bl_idname = "custom.button_operator6"
    bl_label = "Custom Button 6"
    def execute(self, context):
        self.report({'INFO'}, "Button Pressed.")
        return {'FINISHED'}

# Make Instances
class CustomButtonOperator7(bpy.types.Operator):
    bl_idname = "custom.button_operator7"
    bl_label = "Custom Button 7"

    def execute(self, context):
        instances = make_instances()
        self.report({'INFO'}, f"Created {len(instances)} instances.")
        return {'FINISHED'}

def register():
    # handle the keymap
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        km = wm.keyconfigs.addon.keymaps.new(name="Window", space_type='EMPTY')
        kmi = km.keymap_items.new(CustomButtonOperator1.bl_idname, 'D', 'PRESS', ctrl=True, shift=True)
        kmi = km.keymap_items.new(CustomButtonOperator2.bl_idname, 'C', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))

    bpy.utils.register_class(CustomTabPanel3)
    bpy.utils.register_class(CustomTabPanel4)
    bpy.utils.register_class(CustomTabPanel1)
    bpy.utils.register_class(CustomTabPanel2)
    bpy.utils.register_class(CustomButtonOperator1)
    bpy.utils.register_class(CustomButtonOperator2)
    bpy.utils.register_class(CustomButtonOperator3)
    bpy.utils.register_class(CustomButtonOperator4)
    bpy.utils.register_class(CustomButtonOperator5)
    bpy.utils.register_class(CustomButtonOperator6)
    bpy.utils.register_class(CustomButtonOperator7)

    bpy.types.Scene.custom_radio_selection = bpy.props.EnumProperty(
        items=[('INSTANCES', 'Instance', 'Create instances'),
               ('EMPTY', 'Empty', 'Create empty objects')],
        name="Custom Radio Select"
    )
    bpy.types.Scene.custom_delta = bpy.props.FloatProperty(name="Delta", default=0.01)
    bpy.types.Scene.use_scale = bpy.props.BoolProperty(name="Apply Scale", default=True)
    bpy.types.Scene.custom_scale = bpy.props.FloatProperty(name="Scale Multiplier", default=1)
    bpy.types.Scene.path_to_blueprint = bpy.props.StringProperty(name="Path", default="/Game/Items/BP_Item")

def unregister():

    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    del addon_keymaps[:]

    bpy.utils.unregister_class(CustomTabPanel1)
    bpy.utils.unregister_class(CustomTabPanel2)
    bpy.utils.unregister_class(CustomTabPanel3)
    bpy.utils.unregister_class(CustomTabPanel4)
    bpy.utils.unregister_class(CustomButtonOperator1)
    bpy.utils.unregister_class(CustomButtonOperator2)
    bpy.utils.unregister_class(CustomButtonOperator3)
    bpy.utils.unregister_class(CustomButtonOperator4)
    bpy.utils.unregister_class(CustomButtonOperator5)
    bpy.utils.unregister_class(CustomButtonOperator6)
    bpy.utils.unregister_class(CustomButtonOperator7)
    del bpy.types.Scene.custom_text_input

if __name__ == "__main__":
    register()
