let single_gain_random =
    \(elements : List Text) ->
    \(message : Text) -> 
      { type = "single_gain_random"
      , effect = "gain_exp_element_sum"
      , elements = elements
      , message = message
      }
in
 { single_gain_random = 
    [ single_gain_random ["loot", "body_crate"] "{player_name} fights off a small group of Z's. One of them had {a_loot} {on_body}. With this new {loot_category}, they come {time_gain} closer to the next level."
    , single_gain_random ["crate", "loot"] "{in_crate|capitalize}, {player_name} finds {a_loot}. This pushes them {time_gain} towards the next level."
    , single_gain_random ["crate", "loot"] "{player_name} mindlessly checks {in_crate}. To their surprise they find {a_loot}. This propels them {time_gain} towards the next level."
    ]
 }