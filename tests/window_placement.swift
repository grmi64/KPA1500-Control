import Foundation
import CoreGraphics
@main
struct PlacementTests { static func main() {
let screens=[CGRect(x:0,y:0,width:1440,height:900),CGRect(x:-1920,y:0,width:1920,height:1080)]
let normal=CGRect(x:-1700,y:100,width:800,height:600)
assert(WindowPlacement.recover(normal,screens:screens)==normal)
for frame in [CGRect(x:-4000,y:-2000,width:900,height:700),CGRect(x:1000,y:600,width:2000,height:1600),CGRect(x:Double.nan,y:0,width:800,height:600)] {
 let result=WindowPlacement.recover(frame,screens:[screens[0]])
 assert(screens[0].contains(result));assert(WindowPlacement.recover(result,screens:[screens[0]])==result)
}
print("PASS: native meter recovery preserves valid placements and repairs missing screens, oversized and invalid frames.")

} }
