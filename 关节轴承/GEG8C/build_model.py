import bpy, bmesh, math, json, os
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__)); NAME=os.path.basename(OUT)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.001;sc.unit_settings.length_unit='MILLIMETERS'
parts=bpy.data.collections.new('零件_毫米');sc.collection.children.link(parts)
studio=bpy.data.collections.new('预览_灯光相机');sc.collection.children.link(studio)
def link(o,c):
 for a in list(o.users_collection):a.objects.unlink(o)
 c.objects.link(o)
def mat(n,col,metal=.8):
 m=bpy.data.materials.new(n);m.diffuse_color=(*col,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.28;return m
silver=mat('钢制外观_非材质鉴定',(.45,.5,.57));dark=mat('衬层示意',(.045,.055,.065),.1);gold=mat('保持架外观_未确认材质',(.22,.25,.29))
def mesh(n,v,f,material=silver):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(n,me);parts.objects.link(o);o.data.materials.append(material)
 for p in me.polygons:p.use_smooth=len(p.vertices)==4
 return o
def lathe(n,profile,N=128,material=silver):
 v=[(r*math.cos(2*math.pi*i/N),r*math.sin(2*math.pi*i/N),z) for r,z in profile for i in range(N)]
 f=[(j*N+i,j*N+(i+1)%N,((j+1)%len(profile))*N+(i+1)%N,((j+1)%len(profile))*N+i) for j in range(len(profile)) for i in range(N)]
 o=mesh(n,v,f,material)
 for j in range(len(profile)):
  smooth=abs(profile[j][1]-profile[(j+1)%len(profile)][1])>1e-8
  for p in o.data.polygons[j*N:(j+1)*N]:p.use_smooth=smooth
 return o
def ring(n,ri,ro,lo,hi,material=silver):return lathe(n,[(ri,lo),(ro,lo),(ro,hi),(ri,hi)],material=material)
def cyl(n,r,h,z=0,verts=96):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=h,location=(0,0,z+h/2));o=bpy.context.object;o.name=n;link(o,parts);o.data.materials.append(silver);return o
def boolean(a,b,op):
 bpy.context.view_layer.objects.active=a;m=a.modifiers.new(op,'BOOLEAN');m.operation=op;m.solver='EXACT';m.object=b;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(b,do_unlink=True)
def spherical_ball(n,R,bore,width):
 zs=[-width/2+width*i/40 for i in range(41)];p=[(math.sqrt(R*R-z*z),z) for z in zs]+[(bore,width/2),(bore,-width/2)];return lathe(n,p)
def housing(n,R,outer,width):
 zs=[width/2-width*i/36 for i in range(37)];p=[(outer,-width/2),(outer,width/2)]+[(math.sqrt(R*R-z*z),z) for z in zs];return lathe(n,p)
def thread(n,major,pitch,L,z0=0,internal=False):
 N=96;J=math.ceil(L/pitch*16);v=[];root=major/2-.61343*pitch
 for j in range(J+1):
  z=L*j/J
  for i in range(N):
   a=2*math.pi*i/N;dist=abs((z/pitch-a/(2*math.pi))%1-.5);ridge=max(0,min(1,(.4375-dist)/.3125));r=root+(major/2-root)*ridge
   v.append((r*math.cos(a),r*math.sin(a),z+z0))
 f=[tuple(reversed(range(N))),tuple(J*N+i for i in range(N))]+[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(J) for i in range(N)]
 return mesh(n,v,f)
def finish(notes,explode=False):
 checks=[]
 for o in parts.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.to_mesh(o.data);bm.free();assert bad==0 and vol>0,(o.name,bad,vol)
  checks.append({'object':o.name,'nonmanifold_edges':bad,'volume_mm3':round(vol,6),'dimensions_mm':list(o.dimensions)})
 bpy.data.texts.new('尺寸依据与局限').write(notes);open(OUT+'/模型说明.txt','w').write(notes);open(OUT+'/geometry_check.json','w').write(json.dumps(checks,ensure_ascii=False,indent=2))
 # Geometry is saved assembled. Exploded preview only for BA to reveal cage.
 positions={o.name:o.location.copy() for o in parts.objects}
 if explode:
  bpy.data.objects['上垫圈_1mm'].location.z+=7;bpy.data.objects['下垫圈_1mm'].location.z-=4
 bpy.context.view_layer.update();points=[o.matrix_world@Vector(c) for o in parts.objects for c in o.bound_box];lo=Vector([min(p[i] for p in points) for i in range(3)]);hi=Vector([max(p[i] for p in points) for i in range(3)]);target=(lo+hi)/2;s=max(hi-lo)*1.65
 sc.render.engine='CYCLES';sc.cycles.samples=40;sc.cycles.use_denoising=False;sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.world.color=(.25,.25,.25)
 def aim(o):o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 for loc,en,size in [((1,-1,1.7),90,1),((-1,.5,1),100,.8),((1,1,.3),50,1)]:
  bpy.ops.object.light_add(type='AREA',location=target+Vector(loc)*s);o=bpy.context.object;o.data.energy=en*s*s;o.data.size=size*s;aim(o);link(o,studio)
 bpy.ops.object.camera_add(location=target+Vector((1.2,-2,1.1))*s);o=bpy.context.object;aim(o);o.data.type='ORTHO';o.data.ortho_scale=s;sc.camera=o;link(o,studio)
 sc.render.image_settings.file_format='PNG';sc.render.filepath=OUT+'/'+NAME+'_预览.png';sc.render.film_transparent=False;bpy.ops.render.render(write_still=True)
 for n,p in positions.items():bpy.data.objects[n].location=p
 bpy.ops.object.select_all(action='DESELECT');next(iter(parts.objects)).select_set(True);bpy.context.view_layer.objects.active=next(iter(parts.objects))
 for scr in bpy.data.screens:
  for a in scr.areas:
   if a.type=='VIEW_3D':a.spaces.active.region_3d.view_distance=s;a.spaces.active.region_3d.view_location=target
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=OUT+'/'+NAME+'.blend',compress=True)

inner=spherical_ball('可转动球面内圈_孔8宽11',8,4,11)
outer=housing('外圈_外径19宽6',8.025,9.5,6)

finish('GEG8C 自润滑径向关节轴承；名义装配模型。\nLDK厂家尺寸表：d8、D19、B11、C6、球面直径dk16 mm。\n来源 https://www.ldk-bearings.com/geg8c-spherical-plain-bearings-self-lubricating.html （2026-11-13核对）\n独立球面内圈与外圈，可在球心旋转；原点中心，孔沿Z。没有滚珠。衬层未单独实体复原；球面间保留0.025mm显示间隙，未应用制造公差。倒角和润滑衬层细节简化。材质为显示用途，不能认证用户品牌。只供名义装配，不是加工或载荷验证模型。', False)
