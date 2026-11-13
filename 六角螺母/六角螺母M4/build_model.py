import bpy, math, bmesh, json, os
from mathutils import Vector
P={'nominal_diameter': 4, 'across_flats_assumed': 7, 'height_assumed': 3.2, 'pitch_assumed': 0.7, 'reference_url': 'https://www.accu.co.uk/hexagon-nuts/268707-HPN-M4-BR'}
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT);L=P['height_assumed'];D=P['nominal_diameter'];AF=P['across_flats_assumed'];pitch=P['pitch_assumed']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.001;sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.world.color=(.25,.25,.25)
assets=bpy.data.collections.new('零件_毫米尺寸');sc.collection.children.link(assets)
preview=bpy.data.collections.new('预览专用_相机灯光地面');sc.collection.children.link(preview)
def link(o,c):
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o)
mat=bpy.data.materials.new('银色金属_材质牌号未确认');mat.diffuse_color=(.52,.57,.62,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.52,.57,.62,1);bs.inputs['Metallic'].default_value=.9;bs.inputs['Roughness'].default_value=.26
# One closed annular mesh: a hexagonal outside and continuous helical inside.
n=192;vs=[];rows=[]
def ring(z,radii):
 row=[]
 for i,r in enumerate(radii):
  a=2*math.pi*i/n;row.append(len(vs));vs.append((r*math.cos(a),r*math.sin(a),z))
 rows.append(row)
def hexr(a):return AF/2/math.cos((a%(math.pi/3))-math.pi/6)
# Outer hex edge chamfer is simplified, not a measured turned profile.
for z,shrink in [(0,.25),(.25,0),(L-.25,0),(L,.25)]:
 ring(z,[hexr(2*math.pi*i/n)-shrink for i in range(n)])
# Inner mouth and thread traversed downward to close the shell.
steps=math.ceil(L/pitch*28)
for j in range(steps+1):
 z=L*(1-j/steps);rs=[]
 for i in range(n):
  a=2*math.pi*i/n;phase=(z/pitch-a/(2*math.pi))%1
  shape=max(0,min(1,(.4375-abs(phase-.5))/.3125))
  r=D/2-.541266*pitch+.541266*pitch*shape
  mouth=max(0,1-min(z,L-z)/(.55*pitch))
  r=r*(1-mouth)+(D/2+.08)*mouth
  rs.append(r)
 ring(z,rs)
fs=[]
for a,b in zip(rows,rows[1:]+rows[:1]):
 for i in range(n):fs.append((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
me=bpy.data.meshes.new(NAME);me.from_pydata(vs,[],fs);me.update();main=bpy.data.objects.new(NAME,me);assets.objects.link(main);main.data.materials.append(mat)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.to_mesh(me);bm.free();assert bad==0 and vol>0
for f in me.polygons:f.use_smooth=(4*n <= f.index < len(me.polygons)-n)
for k,v in P.items():main[k]=v
notes=f"""{NAME} · 照片参考模型
照片标签仅明确 M{D}，可见为六角螺母；材料、等级及标准号未确认。
参考 DIN 934 同类产品的外形参数：对边 {AF} mm，厚 {L} mm，常用粗牙 {pitch} mm。
尺寸参考来源：{P['reference_url']}
仅借用同类尺寸，不认定用户实物就是该品牌、材料或标准品。
内螺纹为连续右旋近似牙形。倒角、牙根、截顶和公差未实测，不是量规认证或加工模型。
原点为下表面中心，轴向 +Z。单位mm。用于库存识别与装配布局前需核对实测尺寸，尤其螺距和厚度。
修改 P 后用 blender -b --python build_model.py 重建，会覆盖模型和预览，请先备份。
"""+json.dumps(P,ensure_ascii=False,indent=2)
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes);bpy.data.texts.new('尺寸依据与边界').write(notes)
checks={'name':NAME,'nonmanifold_edges':bad,'volume_mm3':vol,'dimensions_mm':list(main.dimensions),'reference_assumptions':P}
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(checks,ensure_ascii=False,indent=2))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
target=(0,0,L/2);scale=AF*1.65
bpy.ops.mesh.primitive_plane_add(size=100,location=(0,0,-.02));o=bpy.context.object;link(o,preview);ground=bpy.data.materials.new('Studio slate');ground.diffuse_color=(.055,.075,.1,1);o.data.materials.append(ground)
for name,loc,en,sz in [('Key',(1,-1.3,1.9),80,1),('Rim',(-1,1,1.3),110,.8),('Fill',(1.5,.5,.5),60,1)]:
 bpy.ops.object.light_add(type='AREA',location=Vector(target)+Vector(loc)*scale);o=bpy.context.object;o.name=name;o.data.energy=en*scale*scale;o.data.size=sz*scale;aim(o,target);link(o,preview)
bpy.ops.object.camera_add(location=Vector(target)+Vector((1.4,-2,1.7))*scale);cam=bpy.context.object;aim(cam,target);cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.camera=cam;link(cam,preview)
sc.render.image_settings.file_format='PNG';sc.render.filepath=os.path.join(OUT,NAME+'_预览.png')
bpy.ops.object.select_all(action='DESELECT');main.select_set(True);bpy.context.view_layer.objects.active=main
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=scale*1.5;area.spaces.active.region_3d.view_location=target
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,NAME+'.blend'),compress=True);bpy.ops.render.render(write_still=True);print('QA',checks)
