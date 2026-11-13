import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
D=json.loads((root/'mesh.json').read_text());bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
allv=[v for p in D['parts'] for v in p['vertices']];c=[(max(v[i] for v in allv)+min(v[i] for v in allv))/2 for i in range(3)]
report=[]
for i,p in enumerate(D['parts']):
 m=bpy.data.meshes.new(p['name']);m.from_pydata([tuple(v[j]-c[j] for j in range(3)) for v in p['vertices']],[],p['faces']);m.update();o=bpy.data.objects.new(p['name'],m);bpy.context.collection.objects.link(o)
 bm=bmesh.new();bm.from_mesh(m);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));report.append({'name':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'volume_mm3':bm.calc_volume(),'bbox_mm':p['bbox_mm']});bm.to_mesh(m);bm.free()
 o['source']='Fusion cached display mesh; not recovered parametric history';o['part_index']=i+1
 mat=bpy.data.materials.new('Aluminum_'+str(i));mat.use_nodes=True;q=mat.node_tree.nodes.get('Principled BSDF');q.inputs['Base Color'].default_value=((.36,.42,.48,1) if i!=1 else (.21,.26,.31,1));q.inputs['Metallic'].default_value=.75;q.inputs['Roughness'].default_value=.32;m.materials.append(mat)
# Original STEP assembly relations preserved; common translation only.
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=.001;s.unit_settings.length_unit='MILLIMETERS';s['source_center_translation_mm']=c;s['source_bbox_mm']=D['bbox_mm']
bpy.ops.object.camera_add(location=(94,-115,78));cam=bpy.context.object;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=175;cam.location.z+=20;cam.rotation_euler=(Vector((0,0,20))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
for pos,power,size in [((50,-70,100),220000,80),((-60,-20,40),140000,60),((20,70,10),180000,65)]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=power;l.data.size=size;l.rotation_euler=(-l.location).to_track_quat('-Z','Y').to_euler()
s.world.color=(.12,.12,.12);s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True;s.render.resolution_x=1100;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(root/'双层20mm宽100mm滑轨_F3D转换_预览.png');s.view_settings.view_transform='AgX'
text=bpy.data.texts.new('先读我');text.write('由用户 slider.f3d 内置显示网格提取，3个独立闭合网格，20×16×100 mm。原F3D保存参数与连接；本Blender未导入Fusion特征树或原生关节。新增轴向示意绑定：底轨固定，中轨移动20mm，上轨再相对移动20mm，然后收回。20mm仅演示量，不是实际行程或原关节限位。修改Motion_Control两个自定义属性可独立移动，不带机械止挡。')

# Newly reconstructed illustrative prismatic controls, not imported Fusion joints.
bpy.ops.object.empty_add();ctrl=bpy.context.object;ctrl.name='Motion_Control_RECONSTRUCTED_DEMO'
ctrl['middle_slide_mm']=0.;ctrl['upper_relative_mm']=0.;ctrl['warning']='20 mm illustrative movement, NOT source joint limits or verified rated travel'
for name,expression,props in [('CenterRail','a',['middle_slide_mm']),('OuterRail_R','a+b',['middle_slide_mm','upper_relative_mm'])]:
 o=bpy.data.objects[name];o.lock_location=(True,True,False);o.lock_rotation=(True,True,True)
 drv=o.driver_add('location',2).driver;drv.expression=expression
 for key,prop in zip('ab',props):
  v=drv.variables.new();v.name=key;v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["'+prop+'"]'
for frame,a,b in [(1,0,0),(25,0,0),(85,20,20),(115,20,20),(175,0,0),(195,0,0)]:
 for prop,val in [('middle_slide_mm',a),('upper_relative_mm',b)]:ctrl[prop]=val;ctrl.keyframe_insert(data_path='["'+prop+'"]',frame=frame)
s.frame_start=1;s.frame_end=195;s.render.fps=30;s.frame_set(1)

bpy.ops.object.select_all(action='DESELECT');parts=[o for o in s.objects if o.type=='MESH'];[o.select_set(True) for o in parts];bpy.context.view_layer.objects.active=parts[0]
for a in bpy.context.screen.areas:
 if a.type=='VIEW_3D': a.spaces.active.region_3d.view_distance=120;a.spaces.active.clip_end=10000
(root/'verification.json').write_text(json.dumps({'source_sha256':D['sha256'],'source_valid':D['valid'],'source_bbox_mm':D['bbox_mm'],'parts':report},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(root/'双层20mm宽100mm滑轨_F3D转换.blend'),compress=True);bpy.ops.render.render(write_still=True)
