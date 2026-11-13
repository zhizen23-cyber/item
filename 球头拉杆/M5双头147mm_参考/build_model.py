import bpy,bmesh,math,json,os
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.001;sc.unit_settings.length_unit='MILLIMETERS'
assets=bpy.data.collections.new('零件_毫米尺寸');sc.collection.children.link(assets)
preview=bpy.data.collections.new('预览专用');sc.collection.children.link(preview)
def link(o,c=assets):
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o)
def mat(name,col,metal=.85,rough=.27):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
steel=mat('钢外观',(.48,.53,.58));dark=mat('内球圈',(.19,.23,.28));brass=mat('衬圈外观_材质未知',(.45,.32,.10))
def mesh(name,vs,fs,m):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);assets.objects.link(o);o.data.materials.append(m)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 return o
def lathe(name,profile,m,n=128):
 vs=[(r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z) for r,z in profile for i in range(n)];fs=[]
 for j in range(len(profile)):
  for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,((j+1)%len(profile))*n+(i+1)%n,((j+1)%len(profile))*n+i))
 o=mesh(name,vs,fs,m)
 for p in o.data.polygons:p.use_smooth=True
 return o
def cyl(name,r,L,loc,m,vertices=96,axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=L,location=loc);o=bpy.context.object;o.name=name;link(o);o.data.materials.append(m)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 return o
def tube(name,points,r,m):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=1;c.bevel_depth=r;c.bevel_resolution=4;c.use_fill_caps=True;s=c.splines.new('POLY');s.points.add(len(points)-1)
 for p,co in zip(s.points,points):p.co=(*co,1)
 o=bpy.data.objects.new(name,c);assets.objects.link(o);o.data.materials.append(m);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();return o

P=dict(overall_length_assumed=147,eye_bore=5,eye_width=8,end_length=37,eye_outer_diameter_assumed=16,center_distance_derived=131,thread_nominal='M5',pitch_assumed=.8)
notes="""依据用户产品图：M5双头147mm，孔径5mm，厚8mm，端头37mm。147mm暂按两端外缘总长解释，非确认孔中心距。
眼外径16、头体厚6、球面R6.5、颈部和六角尺寸及螺纹M5×0.8均为参考假设，不是实测。由假设眼外径推得孔距131mm，不能作为采购/加工确定尺寸。37mm按端头最外缘至连接螺纹入口解释。
两个内球圈为独立对象，原点各在转动中心，可围绕本地X/Y转动观察。±8度仅演示姿态，不是允许偏角/承载验证。中央杆不可据此认定左右旋或调节范围，螺纹牙形为简化螺旋。外壳、颈、六角作为独立制造包络，交叠表示一体件，未冒充可直接加工实体。
单位1 Blender单位=1mm。全长轴X；孔轴Z。该模型用途为库存识别、名义包络和运动方向参考。
"""
for sign in [-1,1]:
 cx=sign*65.5
 o=lathe('端头壳体_外径16假设',[(6.85,-3),(7.7,-3),(8,-2.7),(8,2.7),(7.7,3),(6.85,3)],steel);o.location.x=cx
 o=lathe('衬圈_示意',[(6.82,-3.05),(6.82,3.05)]+[(math.sqrt(6.5**2-z*z)+.08,z) for z in [3.05-i*6.1/32 for i in range(33)]],brass);o.location.x=cx
 prof=[(2.5,-4)]+[(math.sqrt(6.5**2-z*z),z) for z in [-4+i*8/32 for i in range(33)]]+[(2.5,4)]
 ball=lathe('可动内球圈_孔5厚8',prof,dark);ball.location.x=cx;ball['visual_motion_only']=True
 for frame,angle in [(1,0),(40,sign*math.radians(8)),(80,0)]:ball.rotation_euler[0]=angle;ball.keyframe_insert('rotation_euler',frame=frame)
 cyl('端头颈部_参考',3.9,20,(sign*48.5,0,0),steel,axis='X')
 cyl('端头六角_参考',4.6,4,(sign*38.5,0,0),steel,vertices=6,axis='X')
cyl('中央连杆_光杆区',2.5,38,(0,0,0),steel,axis='X')
for sign in [-1,1]:
 cyl('M5螺纹芯_假设牙距0p8',2.05,19,(sign*28.5,0,0),steel,axis='X')
 points=[]
 for i in range(1201):
  x=19+19*i/1200;t=(x-19)/.8*math.tau;points.append((sign*x,2.22*math.cos(t),2.22*math.sin(t)))
 tube('M5可见牙_简化',points,.27,steel)
sc.frame_end=80;sc.frame_set(1);floor=-4.8;camera=(.15,-1,2.8)

bpy.context.view_layer.update()
checks=[]
for o in assets.objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);v=bm.calc_volume(signed=True);bm.free();assert bad==0 and v>0,(o.name,bad,v)
 checks.append(dict(name=o.name,nonmanifold_edges=bad,volume_mm3=v))
pts=[o.matrix_world@Vector(c) for o in assets.objects if o.type=='MESH' for c in o.bound_box];dims=[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)]
report=dict(dimensions_mm=dims,parts=checks,parameters=P,scope='外观与名义包络参考，不是制造图或力学认证')
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(report,ensure_ascii=False,indent=2))
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes);bpy.data.texts.new('尺寸依据与假设').write(notes)
open(os.path.join(OUT,'README.md'),'w').write('# '+NAME+'\n\n![预览]('+NAME+'_预览.png)\n\n'+notes+'\n\n[模型]('+NAME+'.blend) · [参数脚本](build_model.py) · [校验](geometry_check.json)\n')
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=False;sc.render.resolution_x=1100;sc.render.resolution_y=650;sc.render.resolution_percentage=100;sc.world.color=(.28,.28,.28)
scale=max(dims)*1.2;target=Vector((0,0,0))
bpy.ops.mesh.primitive_plane_add(size=scale*6,location=(0,0,floor));o=bpy.context.object;link(o,preview);o.data.materials.append(mat('Studio',(.045,.065,.085),0,.5))
for loc,en,sz in [((.3,-.8,1.8),65,1),((-1,.7,1.6),85,.8),((1.5,.5,.8),35,1)]:
 bpy.ops.object.light_add(type='AREA',location=Vector(loc)*scale);o=bpy.context.object;link(o,preview);o.data.energy=en*scale*scale;o.data.size=sz*scale;aim(o,target)
bpy.ops.object.camera_add(location=Vector(camera)*scale);cam=bpy.context.object;link(cam,preview);aim(cam,target);cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.camera=cam
sc.render.image_settings.file_format='PNG';sc.render.filepath=os.path.join(OUT,NAME+'_预览.png')
bpy.ops.object.select_all(action='DESELECT')
for o in assets.objects:o.select_set(True)
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.region_3d.view_distance=scale;a.spaces.active.region_3d.view_location=target
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,NAME+'.blend'),compress=True);bpy.ops.render.render(write_still=True)
print('QA',report)
