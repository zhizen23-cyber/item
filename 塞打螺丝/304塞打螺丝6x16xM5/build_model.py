import bpy, math, os, bmesh, json
from mathutils import Vector
# All numeric values are millimetres. P drives actual mesh dimensions.
P={'shoulder_d': 6, 'shoulder_l': 16, 'thread_d': 5, 'pitch': 0.8, 'thread_l': 10, 'head_d': 10, 'head_h': 4.35, 'socket_af': 3, 'socket_depth_assumed': 2, 'dark': False, 'label': '6*16*M5 佰瑞特304不锈钢光杆塞打螺栓'}
OUT=os.path.dirname(os.path.abspath(__file__))
NAME=os.path.basename(OUT)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001;scene.unit_settings.length_unit='MILLIMETERS'
D,L,M,p,T,H,K,AF,SD=[P[k] for k in ['shoulder_d','shoulder_l','thread_d','pitch','thread_l','head_d','head_h','socket_af','socket_depth_assumed']]
N=192; rings=[];z0=-L-T;nr=math.ceil(T/p*32)
for j in range(nr+1):
 z=z0+T*j/nr;rr=[]
 for i in range(N):
  a=2*math.pi*i/N;phase=((z-z0)/p-a/(2*math.pi))%1;t=max(0,min(1,(.4375-abs(phase-.5))/.3125));depth=.6134*p
  taper=min(1,(z-z0)/(p*.6),(-L-z)/(p*.5));r=M/2-depth+depth*t*max(0,taper)
  r-=p*.35*max(0,1-(z-z0)/(p*.45));rr.append(r)
 rings.append((z,rr))
c=min(.2,D*.04)
for z,r in [(-L,D/2-c),(-L+c,D/2),(-c,D/2),(0,D/2+c),(0,H/2-c),(c,H/2),(K-c,H/2),(K,H/2-c)]:
 rr=[r]*N
 # 12.9 photo shows dark, straight knurled socket head; groove count/depth estimated.
 if P['dark'] and z in [c,K-c]:rr=[r-(.10 if i%2==1 else 0) for i in range(N)]
 rings.append((z,rr))
verts=[(r[i]*math.cos(2*math.pi*i/N),r[i]*math.sin(2*math.pi*i/N),z) for z,r in rings for i in range(N)]
faces=[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(len(rings)-1) for i in range(N)]
faces +=[tuple(reversed(range(N))),tuple((len(rings)-1)*N+i for i in range(N))]
mesh=bpy.data.meshes.new(NAME+'_连续螺旋实体');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(NAME,mesh);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True)
bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=AF/math.sqrt(3),depth=SD+.4,location=(0,0,K-SD/2+.2));cut=bpy.context.object
bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('内六角槽','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;mod.solver='EXACT';bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
mat=bpy.data.materials.new('12.9_dark_steel' if P['dark'] else '304_stainless');mat.diffuse_color=((.08,.09,.11,1) if P['dark'] else (.48,.52,.57,1));mat.use_nodes=True;b=mat.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=mat.diffuse_color;b.inputs['Metallic'].default_value=.88;b.inputs['Roughness'].default_value=.26;o.data.materials.append(mat)
for k,v in P.items():o[k]=v
notes='304塞打螺丝6x16xM5｜商品尺寸图参考模型，非加工图\n来源：用户2026-11-13提供的佰瑞特商品尺寸图。\n图上明确标注（mm）：光杆直径6、光杆长度16，螺纹M5、长10、螺距0.8，头径10、头高4.35，内六角对边3。名义总长30.35。\n光杆长度不含头和螺纹；头下平面z=0，肩至z=-16，端至z=-26。1 Blender单位=1mm。\n六角槽深暂取2mm，倒角、退刀槽和牙底细部均为参考。真实螺旋方向与名义螺距，非制造认证的完整牙型。\n图注称单批次测量且以实购为准；上述尺寸并非用户卡尺实测。304依据商品说明，不是材料检测。图示包装数量不计为实际库存数量。\n本项为新规格，不覆盖4xM3x3或其他旧肩长。不可依据本模型进行极限配合、强度认证或直接加工。\n'
bpy.data.texts.new('尺寸依据_先读').write(notes);open(os.path.join(OUT,'模型说明.txt'),'w').write(notes)
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));nm=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.to_mesh(o.data);bm.free();assert nm==0 and vol>0
assert all(abs(a-b)<1e-4 for a,b in zip(o.dimensions,(H,H,K+L+T)))
o['validation_nonmanifold_edges']=nm;o['nominal_total_height_mm']=K+L+T
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps({'parameters':P,'envelope_mm':list(o.dimensions),'nonmanifold_edges':nm,'volume_mm3':vol},ensure_ascii=False,indent=2))
open(os.path.join(OUT,'README.md'),'w').write('# '+NAME+'\n\n![预览]('+NAME+'_预览.png)\n\n'+notes+'\n[模型]('+NAME+'.blend)')
col=bpy.data.collections.new('Preview_only');scene.collection.children.link(col)
def move(a):
 for cc in list(a.users_collection):cc.objects.unlink(a)
 col.objects.link(a)
def aim(a,p):a.rotation_euler=(Vector(p)-a.location).to_track_quat('-Z','Y').to_euler()
span=max(H,K+L+T);target=(0,0,(K+z0)/2)
bpy.ops.mesh.primitive_plane_add(size=span*20,location=(0,0,z0-.03));floor=bpy.context.object;move(floor);fm=bpy.data.materials.new('Charcoal');fm.diffuse_color=(.055,.07,.09,1);floor.data.materials.append(fm)
for loc,en,sz in [((.8,-1,1.3),1800,.9),((-.8,.5,.7),2200,.7),((.5,.7,-.1),1400,.8)]:
 bpy.ops.object.light_add(type='AREA',location=tuple(v*span for v in loc));a=bpy.context.object;a.data.energy=en*(span/11)**2;a.data.size=sz*span;aim(a,target);move(a)
bpy.ops.object.camera_add(location=(1.7*span,-2.2*span,1.6*span+target[2]));cam=bpy.context.object;aim(cam,target);cam.data.type='ORTHO';cam.data.ortho_scale=span*1.48;scene.camera=cam;move(cam)
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=False;scene.world.color=(.2,.2,.2);scene.view_settings.view_transform='AgX';scene.render.resolution_x=900;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(OUT,NAME+'_预览.png')
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=target;area.spaces.active.region_3d.view_distance=span*2
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,NAME+'.blend'),compress=True)
bpy.ops.render.render(write_still=True)
print('VALIDATED',NAME,tuple(o.dimensions),nm)
