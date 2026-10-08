# better_equipment

Held-item behavior for the full-stack ROM.

Team-wide when any one party member holds the item: No-Stick Cap, Pecha Scarf, Persim Band, Weather Band, Insomniscope, Sneak Scarf, Trap Scarf, Twist Band. Twist Band also blocks Defense and Special Defense drops.

Ability Monitor (item 39) stops the holder's abilities from activating.

Stat bands give 2 ranks while held in place of the flat stat bonus: Power Band Attack +2, Def. Band Defense +2, Special Band Special Attack +2, Zinc Band Special Defense +2. Lens Scarf is accuracy +2 and Bright Ribbon is evasion +2. The bonus is added in damage calculation on top of the current stage, including a stage that moves already capped at +6, so +6 counts as +8. Attack-side bands count for the attacker, defense-side bands for the target, and Klutz disables them. The team summary screen no longer shows a flat bonus for these items.

Renamed held items. Their old battle effects are removed. Gold Ribbon's sell price is unchanged.

- Life Band (Lockon Specs): move power x1.5, and each damaging attack costs 10% of max HP (current HP stays at least 1).
- Lens Scarf (No-Aim Scope): accuracy rank +2.
- Focus Scarf (Bounce Band): super-effective damage taken is x0.7.
- Bright Ribbon (Gold Ribbon): evasion rank +2.
- PP Scarf (Joy Ribbon): at the start of a floor, restore 1 PP to a random move that is not already full. Stacks with Deep Breather.
- Wish Scarf (Whiff Specs): when the holder attacks, recover HP equal to 1/8 of the HP the target actually lost.
- Expert Band (Patsy Band): super-effective move power x1.5.
- Z-Scarf (Curve Band): while any party member holds it, Z-Gauge gain is doubled.
- Rhythm Scarf (Racket Band): repeating the same attacking move adds 25% power per use, up to 2x. A different move, including a status move, resets it. The first use is 1x.
- Consistent Band (Munch Belt): not-very-effective moves deal at least neutral damage. It no longer raises Attack or Special Attack and no longer drains Belly faster.

Contact is the move's adjacent range: in front, in front plus sides, the 8 surrounding tiles, or in front cutting corners. Straight lines, two-tile ranges, room, and floor ranges are not contact.

Names and descriptions overwrite the existing item string slots (`6773 + id`, `10704 + id`, `12104 + id`).

Eq_ItemIsActive and Eq_Ability call vanilla IsMonster before HasHeldItem. They do not wrap HasHeldItem, EntityIsValid, IsMonster, or IqSkillIsEnabled globally. Eq_BandStage uses the CalcDamage defender in r9.
