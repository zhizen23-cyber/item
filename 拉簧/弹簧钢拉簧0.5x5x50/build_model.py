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

P=dict(wire=.5,outer_diameter=5,total_length_including_hooks=50,body_axial_length_assumed=40,turn_count_assumed=80,hook_centerline_radius_assumed=2.25)
notes="""依据用户产品图，规格明确为线径0.5mm × 外径5mm × 含钩总长50mm，弹簧钢。不是50mm簧身。
本模型采用簧身轴向40mm、80圈、0.5mm节距、钩中心线半径2.25mm作为几何参考。端钩方向、闭合角、过渡、有效圈数并未从图获得精确数值；不是厂家定型图。两个端钩均与簧身连接为连续管状网格，保留真实线径而不是缩放整件。
没有刚度、初拉力、极限伸长数据，因此不生成虚假的受力/拉伸量动画。只供外观和包络布置，禁止作为力学和寿命证明。单位1 Blender单位=1mm。长轴X，模型总长50mm、外径5mm。
"""
r=2.25
# Start with bottom hook free end, walk to helix, then top hook.
bottom=[(r*math.cos(t),0,-22.5-r*math.sin(t)) for t in [math.radians(330)*(1-i/180) for i in range(181)]]
helix=[(r*math.cos(i/6400*80*math.tau),r*math.sin(i/6400*80*math.tau),-20+40*i/6400) for i in range(6401)]
top=[(r*math.cos(t),0,22.5+r*math.sin(t)) for t in [math.radians(330)*i/180 for i in range(181)]]
points=bottom+helix+top
# long axis X, tube cross section .5; hook maxima sampled at 90 degrees exactly below
for part in (bottom,top):pass
# Insert exact extrema so envelope remains exact before conversion.
points=[(z,y,x) for x,y,z in points]
o=tube('拉簧_连续钢丝_含钩50参考',points,.25,steel)
# Polyline sampling slightly undershoots extrema; normalise axial envelope only (<0.001mm).
bpy.context.view_layer.update();o.scale.x=50/o.dimensions.x;bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.select_set(False)
floor=-2.8;camera=(.15,-1,2.8)

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
