let loot =
      \(aLoot : Text) ->
      \(category : Text) ->
      \(worth : Double) ->
        { a_loot = aLoot, category, worth }

let crate =
      \(inCrate : Text) -> \(worth : Double) -> { in_crate = inCrate, worth }

let bodyCrate =
      \(onBody : Text) -> \(worth : Double) -> { on_body = onBody, worth }

in  { loot =
      [ loot "an old rifle" "weapon" 0.3
      , loot "a broken assault rifle" "weapon" 0.7
      , loot "a rusty cap opener" "tool" 0.2
      , loot "some money" "junk" 0.1
      , loot "large stash of rations" "food" 0.8
      , loot "medium stash of rations" "food" 0.5
      , loot "small stash of rations" "food" 0.3
      , loot "a small box of pain-killers" "medicine" 0.5
      , loot "a large, expired box of pain-killers" "medicine" 0.7
      , loot "a rotten banana" "junk" 0.1
      , loot "some metal wire" "material" 0.3
      , loot "some wooden planks" "material" 0.4
      , loot "a bent knife" "tool which is also a weapon" 0.5
      , loot "a brand new, sharp knife" "tool which is also a weapon" 0.9
      , loot "a hammer" "tool which is also a weapon" 0.5
      , loot "a slegehammer" "tool which is also a weapon" 0.8
      , loot "beer" "food" 0.7
      , loot "a pair of scissors" "tool which is also a weapon" 0.7
      , loot "a pair of pliers" "tool" 0.6
      ]
    , crate =
      [ crate "in a hole in the wall" 0.3
      , crate "under a dirty bed" 0.4
      , crate "in a closed cabinet" 0.8
      , crate "under some metal junk" 0.2
      , crate "on a table" 0.6
      , crate "on the backseat of a car" 0.6
      , crate "on a wall" 0.4
      , crate "in the open" 0.1
      , crate "in a hidden cache" 0.3
      ]
    , body_crate =
      [ bodyCrate "in the back pocket" 0.3
      , bodyCrate "in her pants" 0.6
      , bodyCrate "in his pants" 0.6
      , bodyCrate "on their back" 0.8
      , bodyCrate "strapped to their chest" 0.5
      , bodyCrate "in their hand" 0.8
      ]
    }
