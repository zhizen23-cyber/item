import bpy, math, bmesh, json, os
from mathutils import Vector
P={'inner_diameter':6,'outer_diameter':8,'length':35,'chamfer_reference':.15}
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT);L=35;D=8;AF=8
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.001;sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.world.color=(.25,.25,.25)
assets=bpy.data.collections.new('零件_毫米尺寸');sc.collection.children.link(assets)
preview=bpy.data.collections.new('预览专用_相机灯光地面');sc.collection.children.link(preview)
def link(o,c):
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o)
mat=bpy.data.materials.new('黑色金属外观_材质涂层未确认');mat.diffuse_color=(.055,.065,.08,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.055,.065,.08,1);bs.inputs['Metallic'].default_value=.9;bs.inputs['Roughness'].default_value=.3
n=128;vs=[];fs=[]
profile=[(3.85,0),(4,.15),(4,34.85),(3.85,35),(3.15,35),(3,34.85),(3,.15),(3.15,0)]
for r,z in profile:
 for i in range(n):
  a=2*math.pi*i/n;vs.append((r*math.cos(a),r*math.sin(a),z))
for j in range(len(profile)):
 for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,((j+1)%len(profile))*n+(i+1)%n,((j+1)%len(profile))*n+i))
me=bpy.data.meshes.new(NAME);me.from_pydata(vs,[],fs);me.update();main=bpy.data.objects.new(NAME,me);assets.objects.link(main);me.materials.append(mat)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.to_mesh(me);bm.free();assert bad==0 and vol>0
for f in me.polygons:f.use_smooth=abs(f.normal.z)<.99
notes='空心轴套 6×8×35：订单SKU Φ6*8*35；按内径6、外径8、长35 mm解释。不是供应商图纸或实测认证；下单前需核对这一尺寸顺序。倒角0.15mm为参考假设，材质订单标题304，不代表材质检测。无公差、硬度、配合等级依据。用于装配占位，不能决定过盈。'
for k,v in P.items():main[k]=v
notes += '\n用户2026-11-13确认：内径6、外径8、长35mm；顺序不再待确认，倒角公差未实测。\n'
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes);bpy.data.texts.new('尺寸依据与边界').write(notes)
checks={'name':NAME,'nonmanifold_edges':bad,'volume_mm3':vol,'dimensions_mm':list(main.dimensions),'parameters':P}
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(checks,ensure_ascii=False,indent=2))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
target=(0,0,L/2);scale=45
bpy.ops.mesh.primitive_plane_add(size=1000,location=(0,0,-.02));o=bpy.context.object;link(o,preview);ground=bpy.data.materials.new('Studio slate');ground.diffuse_color=(.055,.075,.1,1);o.data.materials.append(ground)
for name,loc,en,sz in [('Key',(1,-1.3,1.9),80,1),('Rim',(-1,1,1.3),110,.8),('Fill',(1.5,.5,.5),60,1)]:
 bpy.ops.object.light_add(type='AREA',location=Vector(target)+Vector(loc)*scale);o=bpy.context.object;o.name=name;o.data.energy=en*scale*scale;o.data.size=sz*scale;aim(o,target);link(o,preview)
bpy.ops.object.camera_add(location=Vector(target)+Vector((1.4,-2,1.7))*scale);cam=bpy.context.object;aim(cam,target);cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.camera=cam;link(cam,preview)
sc.render.image_settings.file_format='PNG';sc.render.filepath=os.path.join(OUT,NAME+'_预览.png')
bpy.ops.object.select_all(action='DESELECT');main.select_set(True);bpy.context.view_layer.objects.active=main
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=scale*1.5;area.spaces.active.region_3d.view_location=target
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,NAME+'.blend'),compress=True);bpy.ops.render.render(write_still=True);print('QA',checks)
