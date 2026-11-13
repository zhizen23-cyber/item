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
 o['source']='User supplied STEP; tessellated mesh, not recovered parametric CAD';o['part_index']=i+1
 mat=bpy.data.materials.new('Aluminum_'+str(i));mat.use_nodes=True;q=mat.node_tree.nodes.get('Principled BSDF');q.inputs['Base Color'].default_value=((.36,.42,.48,1) if i!=1 else (.21,.26,.31,1));q.inputs['Metallic'].default_value=.75;q.inputs['Roughness'].default_value=.32;m.materials.append(mat)
# Original STEP assembly relations preserved; common translation only.
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=.001;s.unit_settings.length_unit='MILLIMETERS';s['source_center_translation_mm']=c;s['source_bbox_mm']=D['bbox_mm']
bpy.ops.object.camera_add(location=(94,-115,78));cam=bpy.context.object;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=95;s.camera=cam
for pos,power,size in [((50,-70,100),220000,80),((-60,-20,40),140000,60),((20,70,10),180000,65)]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=power;l.data.size=size;l.rotation_euler=(-l.location).to_track_quat('-Z','Y').to_euler()
s.world.color=(.12,.12,.12);s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True;s.render.resolution_x=1100;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(root/'双层20mm微型铝合金滑轨_预览.png');s.view_settings.view_transform='AgX'
text=bpy.data.texts.new('先读我');text.write('用户原STEP转换，3个独立可编辑网格。文件内包络20×16×70 mm。保持零件相对位置，仅平移公共中心至原点。没有推断伸缩行程或加入动画，不代表实物测量、载荷及公差验证。原STEP保持不变。')
bpy.ops.object.select_all(action='DESELECT');parts=[o for o in s.objects if o.type=='MESH'];[o.select_set(True) for o in parts];bpy.context.view_layer.objects.active=parts[0]
for a in bpy.context.screen.areas:
 if a.type=='VIEW_3D': a.spaces.active.region_3d.view_distance=120;a.spaces.active.clip_end=10000
(root/'verification.json').write_text(json.dumps({'source_sha256':D['sha256'],'source_valid':D['valid'],'source_bbox_mm':D['bbox_mm'],'parts':report},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(root/'双层20mm微型铝合金滑轨.blend'),compress=True);bpy.ops.render.render(write_still=True)
