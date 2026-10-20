"""Package the shared artwork for macOS and Windows (run on macOS)."""
from pathlib import Path
import struct,subprocess,tempfile

root=Path(__file__).resolve().parents[1]
assets=root/'Assets'
source=assets/'AppIcon-source.png'
with tempfile.TemporaryDirectory(prefix='kpa-icons-') as directory:
    stage=Path(directory)
    iconset=stage/'AppIcon.iconset';iconset.mkdir()
    def resize(size,path):
        subprocess.run(['sips','-z',str(size),str(size),str(source),'--out',str(path)],check=True,stdout=subprocess.DEVNULL)
    for size in (16,32,128,256,512):
        resize(size,iconset/f'icon_{size}x{size}.png')
        resize(size*2,iconset/f'icon_{size}x{size}@2x.png')
    subprocess.run(['iconutil','-c','icns',str(iconset),'-o',str(assets/'AppIcon.icns')],check=True)
    # PNG-backed ICO entries retain alpha on modern Windows; 0 denotes 256px.
    sizes=(16,24,32,48,64,128,256)
    images=[]
    for size in sizes:
        path=stage/f'windows-{size}.png';resize(size,path);images.append(path.read_bytes())
    offset=6+16*len(sizes);entries=[]
    for size,data in zip(sizes,images):
        entries.append(struct.pack('<BBBBHHII',size%256,size%256,0,0,1,32,len(data),offset));offset+=len(data)
    (assets/'AppIcon.ico').write_bytes(struct.pack('<HHH',0,1,len(sizes))+b''.join(entries)+b''.join(images))
print('Created Assets/AppIcon.icns and Assets/AppIcon.ico')
