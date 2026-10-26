#pragma once

// PlayStation prompts: with a DualShock 4 (or another PlayStation pad) the
// game's Xbox button icons in text become the PlayStation buttons in the same
// place ("Press <a> to jump" -> "Press [Cross] to jump"). The SDK maps a pad by
// position (SDL's south button is A), so <a> is Cross, <x> Square, <lb> L1 and
// so on. Sticks and the d-pad keep their icons, which do not name a pad; a
// combo tag ("<x-left>") becomes its stick icon and the button ("<analogleft>+
// [Square]"). Colour, line break and currency tags stay. Back is the touchpad.
//
// With the DualShock 4 icon pack (tools/ds4-icons) installed in naruto.bf, the
// game's own icons are PlayStation ones and the tags stay icons; only <lb> and
// <rb>, which share the shoulder icon with <lt> and <rt> in the game's font,
// move to the pack's L1 and R1 glyphs.
//
// Pure functions without SDK dependencies, so the host test can check them.

#include <string>
#include <string_view>

#include "mods/key_prompts.h"

namespace narutorise::pad_prompts {

// The controller_prompts option: "auto" follows the first connected pad,
// "xbox" keeps the game's icons, "playstation" always shows PlayStation names.
enum class Setting { kAuto, kXbox, kPlayStation };

// The setting a controller_prompts value names, ignoring case; false for an
// unknown value, which leaves `out` unchanged.
bool ParseSetting(std::string_view value, Setting& out);

// Tag name without brackets ("a", "lt") -> PlayStation button ("Cross", "L2").
const key_prompts::Labels& PlayStationLabels();

// The text with each Xbox button tag replaced by "[label]" and each combo tag
// by its direction's stick tag and "+[label]". Stick and d-pad tags, other
// tags, unknown tags and unterminated '<' are kept byte for byte.
std::string ReplaceButtonTags(std::string_view text, const key_prompts::Labels& labels);

// The font glyphs the icon pack draws L1 and R1 in: the game's French shoulder
// glyphs, U+008B and U+008E, unused by English texts.
inline constexpr std::string_view kL1Glyph = "\xC2\x8B";
inline constexpr std::string_view kR1Glyph = "\xC2\x8E";

// The text with <lb> and <rb> replaced by the icon pack's L1 and R1 glyphs;
// every other tag is kept byte for byte.
std::string ReplaceShoulderTags(std::string_view text);

}  // namespace narutorise::pad_prompts
