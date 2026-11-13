import bpy, math, os, json, bmesh
from mathutils import Vector
P={'diameter': 4, 'length': 18, 'knurl_diameter_assumed': 4.12, 'knurl_length_assumed': 3.6, 'teeth_assumed': 24, 'chamfer_assumed': 0.16}
OUT=os.path.dirname(os.path.abspath(__file__))
NAME='中部直纹销轴'+format(P['diameter'],'g')+'x'+format(P['length'],'g')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001;scene.unit_settings.length_unit='MILLIMETERS'
d=P['diameter'];L=P['length'];k=P['knurl_length_assumed'];kd=P['knurl_diameter_assumed'];n=P['teeth_assumed'];N=n*8;c=P['chamfer_assumed']
# Centered straight knurl, approximate non-standard tooth profile.
start=(L-k)/2;end=(L+k)/2
profile=[(0,d/2-c,0),(c,d/2,0),(start-.08,d/2,0),(start,d/2,1),(end,d/2,1),(end+.08,d/2,0),(L-c,d/2,0),(L,d/2-c,0)]
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
o=bpy.data.objects.new(NAME+'_中部直纹_参考几何',mesh);bpy.context.collection.objects.link(o)
for p in mesh.polygons:p.use_smooth=False
mat=bpy.data.materials.new('金属外观_材料牌号未标');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.42,.47,.52,1);bs.inputs['Metallic'].default_value=.85;bs.inputs['Roughness'].default_value=.26;o.data.materials.append(mat)
for key,val in P.items():o[key]=val
o['source']='用户图片 1794545269428.jpg，标签 m4*18 / m2*8'
notes=f'''{NAME}｜照片参考建模，单位 mm
标签可读 m{d:g}*{L:g}，解释为光轴直径 {d:g} mm × 总长 {L:g} mm，不是螺纹规格。
实物中部可见轴向直纹，工程分类采用“中部直纹滚花/搓花销轴”；不能从照片认定为标准精密传动花键。
仅直径与总长依据标签，仍不是实测或公差认证。
参考假定：中段居中，纹长 {k:g} mm，齿顶包络 {kd:g} mm，周向 {n} 齿，谷半径低于光轴 0.035 mm。
两端倒角 {c:g} mm，中部纹路过渡 0.08 mm，均需实测确认；照片有透视，禁止当作比例尺量取。
材料与表面处理未知，材质只作金属外观。齿形采用平滑起伏模拟，不是制造级刀具轮廓。
轴线沿本地 Z，Z=0 到 {L:g} mm，独立闭合可编辑网格；相机、灯光、地面归入仅预览集合。
修改 build_model.py 顶部 P 字典可重新生成。不得据此确定压入孔径或过盈量。
加工/装配前需测量：光轴直径、实际总长、滚花齿顶直径、纹长与位置、齿数/齿形、倒角、材料硬度。
'''
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
scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=False;scene.world.color=(.25,.25,.25);scene.view_settings.view_transform='AgX'
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(OUT,NAME+'_预览.png')
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
