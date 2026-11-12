import bpy, math, os, json, bmesh
from mathutils import Vector
P={'diameter': 5, 'length': 20, 'knurl_diameter_label': 5.15, 'knurl_length_assumed': 4, 'teeth_assumed': 32, 'chamfer_assumed': 0.15}
OUT=os.path.dirname(os.path.abspath(__file__))
NAME='搓花轴'+format(P['diameter'],'g')+'x'+format(P['length'],'g')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001;scene.unit_settings.length_unit='MILLIMETERS'
d=P['diameter'];L=P['length'];k=P['knurl_length_assumed'];kd=P['knurl_diameter_label'];n=P['teeth_assumed'];N=n*8;c=P['chamfer_assumed']
# Actual straight axial lobes at ONE end; continuous, closed mesh. No screw/thread helix.
# Each ring: (z, smooth nominal radius, knurl blend). Tooth crests match LABEL envelope.
profile=[(0,d/2-c,0),(c,d/2,0),(L-k-.08,d/2,0),(L-k,d/2,1),(L-c,d/2,1),(L,d/2-c,0)]
verts=[]
for z,r,blend in profile:
 for i in range(N):
  a=2*math.pi*i/N;t=(1+math.cos(n*a))/2
  # peaks +0.075 mm and narrow roots -0.035 mm; roots are assumed profile
  delta= -.035+(kd/2-d/2+.035)*t
  rr=r+blend*delta
  verts.append((rr*math.cos(a),rr*math.sin(a),z))
faces=[]
for j in range(len(profile)-1):
 for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
faces += [tuple(reversed(range(N))),tuple((len(profile)-1)*N+i for i in range(N))]
mesh=bpy.data.meshes.new(NAME+'_实体直纹');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new(NAME+'_单端直纹_花纹长度待实测',mesh);bpy.context.collection.objects.link(o)
for p in mesh.polygons:p.use_smooth=len(p.vertices)==4
mat=bpy.data.materials.new('金属外观_材料牌号未标');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.42,.47,.52,1);bs.inputs['Metallic'].default_value=.85;bs.inputs['Roughness'].default_value=.26;o.data.materials.append(mat)
for key,val in P.items():o[key]=val
o['source']='同目录 '+NAME+'.jpg 标签与实物照片'
notes=f'''{NAME}｜照片参考建模，单位 mm\n标签可读：名义轴径 {d:g}，总长 {L:g}，花纹外径 {kd:g}。这不是实测/公差认证。\n照片实物为单端局部直纹搓花，不是全长滚花、不是菱形网纹，也不是螺纹。\n花纹长度栏没有可读数值；按照片比例暂取 {k:g} mm，需实测确认。\n其余假定：周向 {n} 齿、花纹谷半径比光轴半径小 0.035 mm、两端倒角 {c:g} mm、过渡长 0.08 mm。\n材料与表面处理未标，材质只作金属外观。模型为闭合实体与真实起伏直纹，齿形不是标准认证。\n尺寸取模型本地 Z 轴方向 0 到 {L:g}，搓花位于 Z 正端；单独网格可编辑。\n修改同目录 build_model.py 顶部 P 字典即可重新生成模型和渲染，所有形状参数均用于几何。\n不能据本模型确定压入孔径/过盈量；先测光轴、齿顶包络及花纹长度再做装配。\n'''
bpy.data.texts.new('尺寸依据与假定').write(notes)
open(os.path.join(OUT,'模型说明.txt'),'w',encoding='utf8').write(notes)
col=bpy.data.collections.new('仅预览_相机灯光地面');scene.collection.children.link(col)
def preview(ob):
 for co in list(ob.users_collection):co.objects.unlink(ob)
 col.objects.link(ob)
def aim(ob,pt):ob.rotation_euler=(Vector(pt)-ob.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=L*15,location=(0,0,-.02));ob=bpy.context.object;preview(ob)
f=bpy.data.materials.new('地面');f.diffuse_color=(.065,.08,.10,1);ob.data.materials.append(f)
for loc,power,size in [((L,-L,L*1.5),L*L*15,L),((-L,L,L),L*L*20,L*.8),((L,L,L*.3),L*L*10,L)]:
 bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.data.energy=power;ob.data.size=size;aim(ob,(0,0,L*.5));preview(ob)
bpy.ops.object.camera_add(location=(L*1.6,-L*2,L*1.6));cam=bpy.context.object;aim(cam,(0,0,L*.52));cam.data.type='ORTHO';cam.data.ortho_scale=L*1.28;scene.camera=cam;preview(cam)
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.world.color=(.25,.25,.25);scene.view_settings.view_transform='AgX'
scene.render.resolution_x=700;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(OUT,NAME+'_预览.png')
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.region_3d.view_distance=L*1.7;a.spaces.active.region_3d.view_location=(0,0,L/2)
bpy.context.view_layer.update();bm=bmesh.new();bm.from_mesh(mesh);bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.free()
assert bad==0 and vol>0
assert abs(o.dimensions.z-L)<1e-5
assert abs(o.dimensions.x-kd)<1e-5 and abs(o.dimensions.y-kd)<1e-5
print('VALIDATED',NAME,tuple(o.dimensions),'nonmanifold',bad,'volume',vol)
scene['geometry_validation']=f'nonmanifold={bad}; positive_volume={vol}; envelope={tuple(o.dimensions)}'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,NAME+'.blend'),compress=True)
bpy.ops.render.render(write_still=True)
