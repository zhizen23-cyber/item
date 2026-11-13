import bpy,bmesh,math,json,os
from mathutils import Vector
P={'d': 6, 'D': 22, 'B': 7, 'source': 'https://www.nsk.com/engineering/636zz-esm-md.html', 'scope': 'ZZ双面金属防尘盖外观装配模型；公称包络据NSK系列尺寸参考，不认定实购物品品牌、游隙或内部规格。', 'shielded': True}
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT)
d,D,B=P['d'],P['D'],P['B'];n=192
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.001;sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=False;sc.render.resolution_x=800;sc.render.resolution_y=800;sc.render.resolution_percentage=100;sc.world.color=(.3,.3,.3)
assets=bpy.data.collections.new('零件_毫米尺寸');sc.collection.children.link(assets)
preview=bpy.data.collections.new('预览专用_相机灯光地面');sc.collection.children.link(preview)
def link(o,c):
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o)
def mat(name,col,metal=.85,rough=.28):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*col,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;return m
steel=mat('轴承钢外观_不声明实际材质',(.51,.56,.61));shield=mat('金属防尘盖外观_细部为近似',(.28,.32,.37),.8,.34);env=mat('包络示意_实际盖型未知',(.28,.43,.56),.5,.35)
checks=[]
def annulus(name,ri,ro,z0,z1,ch,m):
 profile=[(ri+ch,z0),(ro-ch,z0),(ro,z0+ch),(ro,z1-ch),(ro-ch,z1),(ri+ch,z1),(ri,z1-ch),(ri,z0+ch)]
 vs=[(r*math.cos(2*math.pi*i/n),r*math.sin(2*math.pi*i/n),z) for r,z in profile for i in range(n)]
 fs=[]
 for j in range(len(profile)):
  for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,((j+1)%len(profile))*n+(i+1)%n,((j+1)%len(profile))*n+i))
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);assets.objects.link(o);o.data.materials.append(m)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.to_mesh(me);bm.free();assert bad==0 and vol>0
 for f in me.polygons:f.use_smooth=f.index//n not in [0,4]
 checks.append({'object':name,'nonmanifold_edges':bad,'volume_mm3':vol})
 return o
if P['shielded']:
 gap=(D-d)/2;ir=d/2+gap*.26;orr=D/2-gap*.24
 annulus('内圈_装配简化',d/2,ir,0,B,min(.3,gap*.08),steel)
 annulus('外圈_装配简化',orr,D/2,0,B,min(.3,gap*.08),steel)
 # Separate slim covers, no false precision in internal raceway/rolling elements.
 for z in [.22,B-.42]:annulus('金属防尘盖_示意',ir+.05,orr-.05,z,z+.20,.035,shield)
else:annulus('轴承4x10x4_包络_盖型未知',d/2,D/2,0,B,.08,env)
for o in assets.objects:
 o['nominal_bore_mm']=d;o['nominal_OD_mm']=D;o['nominal_width_mm']=B;o['model_scope']='nominal assembly envelope; not internal manufacturing geometry'
notes=f'''{NAME}\n名义装配尺寸：内径 {d} mm × 外径 {D} mm × 宽 {B} mm。\n来源：{P['source']}\n{P['scope']}\n轴向 +Z，原点下端面中心。1 Blender 单位=1mm。\n倒角、内外圈分界直径、防尘盖压纹/厚度均为示意，不是厂家制造尺寸；未建滚珠、保持架和真实滚道。不声明精度等级、游隙、载荷性能或具体品牌。不得用于加工、载荷计算或印证内部碰撞。\n模型目的：库存识别、名义孔径/外径/宽度的装配布置。实际配合公差及轴肩圆角需按所购型号和图纸核对。\nbuild_model.py 可独立重建，同目录文件会覆盖，请先备份。\n'''
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes);bpy.data.texts.new('尺寸依据与边界').write(notes)
open(os.path.join(OUT,'README.md'),'w').write('# '+NAME+'\n\n![建模预览]('+NAME+'_预览.png)\n\n'+notes+'\n\n[Blender模型]('+NAME+'.blend)\n')
pts=[o.matrix_world@Vector(c) for o in assets.objects for c in o.bound_box];dims=[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)]
assert all(abs(a-b)<1e-4 for a,b in zip(dims,[D,D,B]))
report={'name':NAME,'dimensions_mm':dims,'parts':checks,'source':P['source'],'model_scope':P['scope']};open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(report,ensure_ascii=False,indent=2))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
target=(0,0,B*.42);scale=D*1.6
bpy.ops.mesh.primitive_plane_add(size=300,location=(0,0,-.04));o=bpy.context.object;link(o,preview);o.data.materials.append(mat('Studio',(.055,.075,.1),0,.5))
for name,loc,en,sz in [('Key',(1,-1.3,1.9),65,1),('Rim',(-1,1,1.3),90,.8),('Fill',(1.5,.5,.5),45,1)]:
 bpy.ops.object.light_add(type='AREA',location=Vector(target)+Vector(loc)*scale);o=bpy.context.object;o.name=name;o.data.energy=en*scale*scale;o.data.size=sz*scale;aim(o,target);link(o,preview)
bpy.ops.object.camera_add(location=Vector(target)+Vector((1.4,-2,2))*scale);cam=bpy.context.object;aim(cam,target);cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.camera=cam;link(cam,preview)
sc.render.image_settings.file_format='PNG';sc.render.filepath=os.path.join(OUT,NAME+'_预览.png')
bpy.ops.object.select_all(action='DESELECT')
for o in assets.objects:o.select_set(True)
bpy.context.view_layer.objects.active=list(assets.objects)[0]
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=scale*1.5;area.spaces.active.region_3d.view_location=target
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,NAME+'.blend'),compress=True);bpy.ops.render.render(write_still=True);print('QA',report)
