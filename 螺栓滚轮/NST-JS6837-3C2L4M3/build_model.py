import bpy,bmesh,math,json,os
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT)
n=128
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

def cyl(name,r,z0,z1,m):
 bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=r,depth=z1-z0,location=(0,0,(z0+z1)/2));o=bpy.context.object;o.name=name;link(o,assets);o.data.materials.append(m);return o
def ball(name,r,z,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=r,location=(0,0,z));o=bpy.context.object;o.name=name;link(o,assets);o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o
def helix(name,r,z0,z1,turns,wire,m):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=wire/2;c.bevel_resolution=4;c.use_fill_caps=True;s=c.splines.new('POLY');N=int(turns*64);s.points.add(N)
 for i,p in enumerate(s.points):
  t=i/N;p.co=(r*math.cos(t*turns*2*math.pi),r*math.sin(t*turns*2*math.pi),z0+t*(z1-z0),1)
 o=bpy.data.objects.new(name,c);assets.objects.link(o);o.data.materials.append(m);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);return o

WIDTH=7;HEIGHT=9
annulus('轴承外圈_旋转件_内部示意',2.65,3.5,0,3,.08,steel)
annulus('轴承内圈_固定件_孔径假设3',1.5,1.95,0,3,.06,steel)
for z in [.18,2.62]:annulus('盖片_金属盖示意_采购盖型未定',1.98,2.62,z,z+.2,.025,shield)
cyl('固定芯轴_内部示意',1.5,0,5,steel)
cyl('台阶_C2_直径暂定4',2,3,5,steel)
cyl('M3螺纹芯_L4',1.2,5,9,steel)
# nominal crest 3mm, simplified helical wire, not manufacturing flank geometry
helix('M3x0p5_螺纹示意',1.35,5.15,8.85,7.4,.3,steel)
notes='尺寸来自诺锶特商品图NST-JS6837-3C2L4M3：外径7、轴承宽3、台阶轴向C=2、M3螺纹L=4mm，总轴向包络9mm。轴承钢+不锈钢螺丝为厂商说明。原点轴承前端面，+Z指向螺纹，1单位=1mm。外圈单独可选旋转，内圈与芯轴分开。商品图未标芯轴/台阶直径、滚道、滚珠、盖型、驱动槽，因此台阶Ø4、内孔Ø3、圈界面与金属盖仅视觉假设，不可据此制造或验证内部碰撞；未建真实滚珠/保持架。M3螺距暂按常用0.5，螺旋牙为示意非精确牙型。装配主包络可以参考，公差/载荷/盖型以实购为准。'

bpy.context.view_layer.update()
report={'source':'用户2026-11-13提供的尺寸商品图','scope':notes,'objects':[]}
for o in assets.objects:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.to_mesh(o.data);bm.free();assert bad==0 and vol>0,(o.name,bad,vol)
 report['objects'].append({'name':o.name,'dimensions_mm':list(o.dimensions),'nonmanifold':bad,'volume_mm3':vol})
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(report,ensure_ascii=False,indent=2))
bpy.data.texts.new('尺寸依据与边界').write(notes)
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes)
open(os.path.join(OUT,'README.md'),'w').write('# '+NAME+'\n\n![预览]('+NAME+'_预览.png)\n\n'+notes+'\n\n[模型]('+NAME+'.blend)')
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
target=(0,0,HEIGHT*.42);scale=max(WIDTH,HEIGHT)*1.65
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
