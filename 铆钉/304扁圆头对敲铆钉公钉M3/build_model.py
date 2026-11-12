import bpy, math, bmesh, json, os
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
# Parameters in mm. *_assumed entries require physical measurement.
P = {'kind': 'male', 'body_diameter': 2.05, 'body_length': 3, 'head_diameter_assumed': 5.5, 'head_height_assumed': 0.8}
OUT=os.path.dirname(os.path.abspath(__file__))
NAME=os.path.basename(OUT)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001;scene.unit_settings.length_unit='MILLIMETERS'
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.world.color=(.35,.35,.35);scene.view_settings.view_transform='AgX'
metal=bpy.data.materials.new('304 Stainless Steel');metal.diffuse_color=(.5,.55,.61,1);metal.use_nodes=True
bs=metal.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.5,.55,.61,1);bs.inputs['Metallic'].default_value=.85;bs.inputs['Roughness'].default_value=.28
assets=bpy.data.collections.new('零件_毫米尺寸');scene.collection.children.link(assets)
preview=bpy.data.collections.new('预览专用_相机灯光地面');scene.collection.children.link(preview)
def link(o,col):
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o)
def lathe(name,profile):
 # Profile runs up outside then down inner wall (female) or to axis (solid).
 n=128;v=[];rows=[]
 for r,z in profile:
  if r==0: rows.append([len(v)]);v.append((0,0,z))
  else:
   rows.append(list(range(len(v),len(v)+n)))
   v.extend([(r*math.cos(2*math.pi*i/n),r*math.sin(2*math.pi*i/n),z) for i in range(n)])
 f=[]
 for a,b in zip(rows,rows[1:]):
  for i in range(n):
   if len(a)==1:f.append((a[0],b[(i+1)%n],b[i]))
   elif len(b)==1:f.append((a[i],a[(i+1)%n],b[0]))
   else:f.append((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(v,[],f);mesh.update()
 o=bpy.data.objects.new(name,mesh);assets.objects.link(o);o.data.materials.append(metal)
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 for face in mesh.polygons:
  face.use_smooth=abs(face.normal.z)<.95
 for k,val in P.items():o[k]=val
 return o
def eclip(d,outer,t):
 # Unstressed E-clip approximation with three inner contact lands; not a standard certified outline.
 ro=outer/2;ri=d/2;pts=[]
 for i in range(161):
  a=math.radians(50+260*i/160);pts.append((ro*math.cos(a),ro*math.sin(a)))
 for i in range(160,-1,-1):
  deg=50+260*i/160;a=math.radians(deg)
  dd=min(abs(deg-x) for x in [68,180,292]);rr=ri if dd<13 else min(ro*.78,ri*1.32)
  pts.append((rr*math.cos(a),rr*math.sin(a)))
 n=len(pts);v=[(x,y,z) for z in [-t/2,t/2] for x,y in pts];f=[]
 for i in range(n):f.append((i,(i+1)%n,(i+1)%n+n,i+n))
 # Triangulate concave caps.
 vectors=[Vector((x,y,0)) for x,y in pts]
 for tri in tessellate_polygon([vectors]):
  ids=[x if isinstance(x,int) else vectors.index(x) for x in tri];f.append(tuple(reversed(ids)));f.append(tuple(i+n for i in ids))
 m=bpy.data.meshes.new('E_clip_outline_assumed');m.from_pydata(v,[],f);m.update();o=bpy.data.objects.new('GB896_开口挡圈_M%d_轮廓待实测'%d,m);assets.objects.link(o);o.data.materials.append(metal)
 bm=bmesh.new();bm.from_mesh(m);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
 return o
if P['kind']=='pin':
 d=P['diameter'];L=P['underhead_length'];h=P['head_height_assumed'];R=P['head_diameter_assumed']/2;c=P['edge_chamfer_assumed'];g=P['groove_diameter_assumed']/2;gw=P['groove_width_assumed'];gc=h+L-P['groove_center_from_end_assumed']
 profile=[(0,0),(R-c,0),(R,.15*h),(R,.8*h),(R-c,h),(d/2,h),(d/2,gc-gw/2),(g,gc-gw/2),(g,gc+gw/2),(d/2,gc+gw/2),(d/2,h+L-c),(d/2-c,h+L),(0,h+L)]
 main=lathe('304_带槽销轴_无螺纹_D%d_L%d'%(d,L),profile)
 clip=eclip(P['clip_nominal'],P['clip_outer_diameter_assumed'],P['clip_thickness_assumed'])
 clip.location=(P['clip_outer_diameter_assumed']*.8,0,gc)
 clip['presentation']='为看清槽与挡圈，沿 X 轴作爆炸偏置。装配时 X=0，Z 保持槽中心。轮廓仅参考。'
 clip['nominal_designation']='GB896 M'+str(P['clip_nominal'])
 extent=L+h;target=(d*.4,0,extent*.5);floor_z=-.03;scale=extent*1.25
 notes='照片标注为 304 带槽销轴 M%d×%d，配 304 开口挡圈 GB896 M%d。M 在此是商家规格写法，本体为光轴，没有螺纹。\n直径 %d、头下长度 %d mm 按规格解释；长度是否含头仍需实测确认。\n挡圈是独立可编辑对象，预览沿 X 轴爆炸偏置；将其 X 设 0 可回到槽中心。\n'%(d,L,P['clip_nominal'],d,L)
else:
 D=P['body_diameter'];L=P['body_length'];H=P['head_height_assumed'];R=P['head_diameter_assumed']/2;c=.08
 # Shallow rounded head below shank, cap's decorative curvature is deliberately modest.
 profile=[(0,0),(R*.55,.04*H),(R*.88,.25*H),(R,.6*H),(R,.85*H),(R-.08,H),(D/2,H),(D/2,H+L-c),(D/2-c,H+L)]
 if P['kind']=='female':
  ri=P['bore_diameter']/2;bottom=H+P['bore_bottom_above_head_assumed']
  profile += [(ri+.05,H+L),(ri,H+L-.06),(ri,bottom),(0,bottom)]
  main=lathe('304_扁圆头紧打母钉_D3_L%d_内径2'%L,profile)
  notes='照片包装明确标 Φ3×%d，内径 2。按外径 3、头下筒长 %d、内径 2 mm 建模。\n可见实物是光孔母钉，不是内螺纹螺母；孔按盲孔建模，孔底位置尚未确认。\n'%(L,L)
 else:
  # Smooth press-fit male stud; M3 is the seller's size designation, not evidence of a thread.
  profile += [(0,H+L)];main=lathe('304_对敲铆钉公钉_M3配套_杆径待实测',profile)
  notes='包装只标“304 扁圆头对敲铆钉（公钉）M3”，没有杆长、杆径或尺寸图。\n实物为光杆对敲公钉，未建螺纹。M3 仅保留为商品规格，不据此假定杆径就是 3 mm。\n为与内径 2 mm 母钉展示配对，暂设公钉杆径 2.05、杆长 3 mm；这不是实测，也不是已验证的过盈量。\n'
 extent=H+L;target=(0,0,extent*.5);floor_z=-.03;scale=max(extent,P['head_diameter_assumed'])*1.65
notes+='所有尺寸单位 mm。以下参数中带 assumed 的值均为照片参考估计/占位，不可作为加工、公差或采购配合保证。\n'+json.dumps(P,ensure_ascii=False,indent=2)+'\n模型为未铆接、未变形状态；未模拟敲入过盈、弹性变形及承载。改变本脚本 P 参数后可重建。原始 JPG 未改。\n重建命令：blender -b --python build_model.py\n'
if P['kind']=='male':notes+='body_diameter 和 body_length 也是假定值，只有 M3 商品标识来自包装。\n'
open(os.path.join(OUT,'模型说明.txt'),'w',encoding='utf8').write(notes);bpy.data.texts.new('尺寸来源与假定_请先读').write(notes)
main['source_photo']=NAME+'.jpg';main['not_manufacturing_certified']=True
# Geometry QA, excluding display objects.
checks=[]
for o in assets.objects:
 bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);bm.free();checks.append({'object':o.name,'nonmanifold_edges':bad,'vertices':len(o.data.vertices)})
 if bad:raise RuntimeError(str(checks))
main['geometry_check']=json.dumps(checks,ensure_ascii=False)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=scale*10,location=(0,0,floor_z));o=bpy.context.object;link(o,preview)
mat=bpy.data.materials.new('Studio slate');mat.diffuse_color=(.055,.075,.10,1);o.data.materials.append(mat)
for name,loc,en,sz in [('Key',(1,-1.3,1.9),80,1),('Rim',(-1,1,1.3),110,.8),('Fill',(1.5,.5,.5),60,1)]:
 bpy.ops.object.light_add(type='AREA',location=Vector(target)+Vector(loc)*scale);o=bpy.context.object;o.name=name;o.data.energy=en*scale*scale;o.data.size=sz*scale;aim(o,target);link(o,preview)
bpy.ops.object.camera_add(location=Vector(target)+Vector((1.4,-2,1.3))*scale);cam=bpy.context.object;aim(cam,target);cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam;link(cam,preview)
scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(OUT,NAME+'_预览.png')
bpy.ops.object.select_all(action='DESELECT');main.select_set(True);bpy.context.view_layer.objects.active=main
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=scale*1.5;area.spaces.active.region_3d.view_location=target
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,NAME+'.blend'),compress=True)
bpy.ops.render.render(write_still=True)
print('GEOMETRY_QA',checks)
