let single_gain_random =
      \(elements : List Text) ->
      \(message : Text) ->
        { type = "single_gain_random", effect = "gain_exp_element_sum", elements, message }

let player_fight =
      \(success_message : Text) ->
      \(fail_message : Text) ->
        { type = "player_fight", success_message, fail_message }

in  { single_gain_random =
      [ single_gain_random
          [ "loot", "body_crate" ]
          "{player_name} fights off a small group of Z's. One of them had {a_loot} {on_body}. With this new {loot_category}, they come {time_gain} closer to the next level."
      , single_gain_random
          [ "crate", "loot" ]
          "{in_crate|capitalize}, {player_name} finds {a_loot}. This pushes them {time_gain} towards the next level."
      , single_gain_random
          [ "crate", "loot" ]
          "{player_name} mindlessly checks {in_crate}. To their surprise they find {a_loot}. This propels them {time_gain} towards the next level."
      ]
    , player_fight =
      [ player_fight
          "Annoyed and hungry, {player_name} defeats {other_player} in a fist fight, which gains them {time_diff} experience."
          "Annoyed and hungry, {player_name} gets into a fist fight with {other_player} and loses them {time_diff}."
      , player_fight
          "{player_name} sneaks up on a sleeping {other_player} and steals their shoes, gaining them {time_diff}."
          "{player_name} is caught trying to sneak up on a sleeping {other_player}. The ensuing beating costs them {time_diff}."
      ]
    }
