## The map at a glance

* **Shack:** outer footprint X -18..18, Z -11..11 (walls 1 thick), so the room inside is
  **34 x 20** (X -17..17, Z -10..10), the largest your addendum allowed: every work spot has
  4 studs of counter of its own and the middle stays empty. Floor top Y 0.4 (2 x 2 black and
  white checker tiles), ceiling Y 9.4 (9 above the floor), a dark 2.4-tall attic over it,
  flat roof Y 12.2..13.4 with parapet and green coping, red corner pilasters, a brick
  chimney from the oven up through the roof, and the big brick **PIZZA** sign on the roof
  front (letters 6 tall, 28 `Bulb`s round it).
* **Openings:** serving window X -5..5, sill Y 3.4 (3.0 above the floor), 3.6 tall, with a
  steel counter inside, a steel ledge outside, the shutter box, side posts and the striped
  awning (out to Z 17, underside Y 9.0). Back door X -17..-13 in the north wall. Side window
  in the west wall Z -6..-2, sill Y 4.2, 2.8 tall (glass), the bench under it inside.
* **Inside, clockwise** (your addendum's order): north wall west to east BackDoor, Fridge,
  DoughStation, SauceStation (WorkSauce then WorkCheese, 4 studs each), ChopStation,
  ToppingRail; east wall north to south Oven, PeelRack, CutTable (Bin on the floor between
  it and the box table), BoxStation; south wall PlushieShelf and RulesBoard above, Register,
  ServingWindow, ShutterButton, CCTVDesk, Sink; west wall StorageShelf, DrinksCooler, the
  side window and bench, FuseBox by the back door. Ceiling: CeilingLamp1, CeilingLamp2,
  Hatch. The empty middle is about 26 x 11 (X -13..13, Z -5..6); `Inspector_Rise` is at its
  centre.
* **Front (Z 11..23):** paved apron and pavement, menu board on the wall east of the
  window, StreetLamp at the kerb west of the queue, bench and litter bin against the wall,
  two bollards, the RoadSign (pole sign with an arrow and the pizza-slice mascot) east of
  the queue. The queue runs south from the window: Queue1 (= `ServingWindow.Customer`),
  Queue2, Queue3, 4 apart.
* **Road:** X -165..165 (it runs off into the dark past both ends), kerbs Z 23..24 and
  47..48, asphalt Z 24..47 a plate below the pavement (Y -0.4): two 11-wide lanes and a
  worn dashed centre line (Z 35..36, some dashes faded or gone). BusStop shelter at X 37..43
  on the near pavement. Across the road: a grass verge, a ditch (Z 49..55, 1.6 deep, a strip
  of dark water), the old billboard and more forest.
* **Back yard:** X -28..28, Z -47..-11, gravel, plank fence 6.4/7.2 tall all round (planks
  alternate height and colour), YardGate X 8..12 in the north fence, delivery pad (concrete,
  Y 0.4 top) just inside it, pavers from the back door, Generator under a lean-to at
  (-20, -34), Dumpster and two wheelie bins at (20, -31), YardLamp on a wooden pole with its
  cable to the shack, two pallets. A dirt path leaves the gate north into the trees.
* **Forest:** 210 brick trees of four kinds, 6 parts each: tall, medium and wide pines (a
  trunk and 5 stacked studded leaf slabs, turned to random angles) and 19 dead snags (a
  trunk and 4 bare branches with a broken top). They reach out to X +-150, Z +-100, none
  within the clearing around the shack, yard and front (X -46..46, Z -60..22), the road
  corridor or the path, and they thin out towards the clearing so the tree line reads from
  the shack.

## What I did differently, and why

1. **Room 34 x 20** (your addendum) and everything outside pushed out to match: front strip
   Z 11..23, road Z 23..48, yard X -28..28, Z -47..-11, generator (-20, -34), dumpster
   (20, -31). The gate stays at X 10 (X 8..12).
2. **Doors are 6.4 tall** (6.5 is off the 0.4 plate grid). The back door has a 0.2 sill, so
   its opening is Y 0.6..7.0.
3. **Counters:** the north counters have a 4-deep work surface (pizza 3.4 + margins) in
   front of a 1-deep raised back shelf (one plate up), 5 deep in total: the ToppingRail's
   six tubs, the flour bin, the sauce pot, the cheese and grater and the knife block stand
   on it. South and east counters are 4 deep (the pizza box is 4). Work surfaces are
   Y 3.4 (boards on top Y 3.8).
4. **Oven** on the east wall Z -6..1 (7 wide, 4 deep, front face X 13) with a solid brick
   chimney breast filling the NE corner just north of it (X 13..17, Z -10..-6), against which
   the ToppingRail counter ends; the chimney rises from the breast through the roof. Two
   5-wide deck openings, floors Y 2.2 and Y 5.0, so the lower deck is waist high and the
   upper one at eye height.
5. **Fridge:** open-fronted, no doors (your addendum), 4 x 4, with a cold light strip.
6. **Sink** was not in your new station order, so I kept it out of the cooking line: it sits
   in the south-west corner with the FireExtinguisher on its bracket on the wall above.
   The CCTVDesk therefore sits just west of the ShutterButton (X -13..-7) instead of in the
   corner.
7. **PlushieShelf** is on the south wall above the BoxStation, just east of the RulesBoard
   (both are above the register end of the wall, there is no room for both directly above
   the till).
8. **RulesBoard.Face** is 7 x 5 x 0.2, dark green (a chalkboard, so light text pops),
   SmoothPlastic, its Front face (-Z) looks into the room: use a SurfaceGui with Face = Front.
   Same for the two monitor `Screen`s (2.4 x 1.8 x 0.2, Front faces the player).
9. **SauceStation** has one `Stand` in the middle plus `StandSauce` and `StandCheese` in
   front of each spot.
10. **BoxStation** is a folding table; the flat boxes are stacked underneath it.
11. **Queue1 = ServingWindow.Customer**: both at (0, 0, 13.5), 2.5 from the wall, facing the
    window.
12. **Cars** use the near (north) lane, driving west as right-hand traffic would:
    Car_Start (140, -0.4, 29.5) -> Car_Stop in front of the window -> Car_End (-140, -0.4,
    29.5), all facing west. Turn them round if your traffic should go the other way.
13. **Truck_Stop** is on the dirt path 11 studs north of the gate, facing south (the way a
    truck arrives from the forest).
14. **Cameras:** each `Cam_` marker has a small visible CCTV camera prop just behind it
    (`Outside.Cameras`). Cam_Front hangs under the awning beside the window and looks down at
    Queue1 three-quarter on, so faces show; Cam_Back is on the street lamp; Cam_Yard on the
    back wall; Cam_Road high on the road sign, looking east along the road at oncoming cars.
15. **Bin** (your addendum): a pedal bin with a hinged `Lid`, standing on the floor against
    the counters between the CutTable and the BoxStation.
16. **Mascot:** the RoadSign carries a stepped pizza-slice body with arms and pepperoni; its
    `Head` (chef's head, face and hat welded on) turns about Y at the neck.
17. **Extras I added** because they help the mood or your code: an attic over the Hatch,
    an EXIT sign and a caged lamp at the back door, the menu board, bollards, pallets,
    trash bags by the dumpster (real `TrashBag` items), the yard lamp's cable, a puddle in
    the ditch. The generator's `Bulb` starts unlit (dark red SmoothPlastic); its lit colour is
    in the Generator Model's attribute `BulbOnColor` ("255,70,40").

