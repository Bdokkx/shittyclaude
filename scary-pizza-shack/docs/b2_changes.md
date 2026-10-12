## What I built differently from the order, and why

The names, the R6 parts and the six joint names are exactly as ordered. These are the places
where I chose something the order did not spell out, or did it another way:

1. **Inspector: 1.7 times as tall, but slim.** A uniform 1.7x R6 is a wide friendly block,
   so he is 1.7x in height only: Torso 2.4 x 3.4 x 1.2 (a plain 1.7x would be 3.4 x 3.4 x
   1.7), legs 1.2 x 3.4 x 1.2, arms 0.85 thick and 4.25 long (1.7 x 1.25 x 2, so his hands
   hang at his knees), long-fingered hands under white cuffs. The Head part is 1.4x (2.8 x
   1.4 x 1.4) so that the black hat with its wide brim (4.1 across) tops out at exactly 9.8;
   `HumanoidRootPart` is at 5.1, as ordered. The joints are the standard R6 ones moved to
   these part sizes (table above), so R6 animations play on him; the Watcher works the
   same way at 1.18x with 1.3x arms.
2. **Humanoid and Animator** inside the Watcher and the Inspector (RigType R6, name and
   health display off), so batch-3 animations load straight onto them. Delete the Humanoid
   if your code adds its own.
3. **Hand items** sit on a grip line through the fist (Right Arm, y = -0.82) and point
   forward out of the front of the fist, as ordered. The one exception is the Umbrella: it
   points forward and 30 degrees down, carried like a walking stick, so its tip stays off the
   ground instead of sticking out 2.7 studs at hip height.
4. **Attributes on the kit pieces:** `Category` (Hair, Hat, Face, Torso, Hand) and
   `BodyPart` (Head, Torso, Right Arm) on every piece, and `HidesHair = true` on the Hood, so
   your code can pick and fit pieces without a name list. The DogLead has an Attachment
   `LeadEnd` in its Handle at the end of the lead, for your Beam or RopeConstraint to the
   dog.
5. **DeliveryTruck `RearDoor`** is a roll-up door, but it cannot slide straight up: the box
   has no room above the opening, so a 7-stud slide would come out through the roof. It is
   one ribbed mesh with its pivot on its top edge and the attribute `OpenTravel = 7`. To
   open it, shrink it from the bottom and keep the top edge where it is (the ribs bunch up
   like a door rolling into the roof):

   ```lua
   local door = truck.RearDoor
   local full = door.Size.Y                                 -- read these while it is shut
   local top = door.CFrame * CFrame.new(0, full / 2, 0)     -- its top edge
   local function setOpen(t)                                -- 0 = shut, 1 = open
       local h = full - (full - 0.6) * t
       door.Size = Vector3.new(door.Size.X, h, door.Size.Z)
       door.CFrame = top * CFrame.new(0, -h / 2, 0)
   end
   ```
6. **Van:** the back opening is 7.6 wide and 6 tall (floor 1.6 to 7.6), not the full inside
   height: the `Sign` you asked for needs a header above the opening to hang on (the header
   runs from 7.6 to 10.6, and the Sign sits on it). Inside, the box is exactly 7.6 wide, 8.2
   tall and 11 long, which is what `Zone` fills. The rear wheels come up through the floor
   as two low boxed benches along the walls (`WheelHousing`), at the back half; the crates
   and pizza boxes stand against the front wall (`Bulkhead`), so the middle of the floor is
   clear for four R6. The `Ramp` is a WedgePart from the ground up to the floor lip, 6 wide
   and 4 long, behind the doors; the doors close above it. `DoorR` carries a thin seam
   strip (welded) that covers the gap between the shut doors. The shell is 8.4 wide and 19
   long as ordered, 10.2 to the roof; the header over the doors stands 0.4 higher (10.6:
   a whole-stud plate, for the brick grid). The side boards and wheel hubs stand 0.2 proud
   of the shell on each side, and the bumper, floor lip and tail lights add a little at the
   ends (the table gives both sizes).
7. **OvenMitts** are two Accessories, `OvenMittL` (LeftGripAttachment) and `OvenMittR`
   (RightGripAttachment), inside a Model `OvenMitts`: an Accessory has one Handle and one
   attachment, so one Accessory cannot follow both hands. Put the pair on with
   `for _, a in Uniforms.OvenMitts:GetChildren() do humanoid:AddAccessory(a:Clone()) end`.
8. **Uniform HiVisVest** uses the same meshes as the CustomerKit HiVisVest
   (`KitHiVisVest__*`), as an Accessory on BodyFrontAttachment. The **Headset** uses
   `HairAttachment` (on an R6 head that is the same point as HatAttachment), so it reads as
   something worn under a hat rather than a hat. The **NameTag**'s `Tag` part has a flat
   Front face for a SurfaceGui with the player's name.
9. **Vehicle `Base`** is an invisible 4 x 0.4 x 8 Part with no collisions, and the vehicle's
   pivot is on the ground under the middle, so
   `van:PivotTo(CFrame.new(x, groundY, z) * CFrame.Angles(0, yaw, 0))` stands the wheels on
   the ground. The lights are lit: each `Headlight` holds a SpotLight `Light` (shining
   forward, range 40), the `Beacon` a red PointLight, the Van's `Bulb` a warm PointLight;
   switch them with `Light.Enabled`.
10. **Flat parts for your text** (`SideL` / `SideR` on the truck and the van, the van's
    `Sign`) are 0.2 thick, have their Front face pointing outwards and their top edge up,
    so a SurfaceGui with Face = Front reads the right way round.
11. **The Passenger's Head** is a separate part on a Motor6D `Neck` (in its Handle), so it
    can turn its head towards the camera; the two `Eye` parts are welded to the Head. The
    Watchdog's and the NightOwl's heads are on a Motor6D `Neck` in the plush's `Body` in
    the same way, with the pivot at the neck as ordered.
12. **InspectorHole** scales with `Model:ScaleTo(width / 8)`, 3 to 8 studs. `Dark` is the
    PrimaryPart, a black Neon disc (Neon, so no light ever greys it), and the Model's pivot
    is at floor level in the middle, so `hole:PivotTo(CFrame.new(x, floorY, z))` sits it on
    the floor. The tiles are two meshes (`TilesLight`, `TilesDark`, one per checker colour)
    lifted at the inner edge as if pushed up from below.
