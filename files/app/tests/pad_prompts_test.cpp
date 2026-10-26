#include <iostream>
#include <stdexcept>
#include <string>

#include "mods/pad_prompts.h"

using namespace narutorise::pad_prompts;
namespace {
unsigned checks = 0;
void Check(bool value, const char* label) {
  ++checks;
  if (!value)
    throw std::runtime_error(label);
}
void Equal(const std::string& actual, const std::string& expected, const char* label) {
  ++checks;
  if (actual != expected)
    throw std::runtime_error(std::string(label) + ": got \"" + actual + "\", expected \"" +
                             expected + "\"");
}

std::string Replace(std::string_view text) {
  return ReplaceButtonTags(text, PlayStationLabels());
}

void SettingTests() {
  auto setting = Setting::kXbox;
  Check(ParseSetting("auto", setting) && setting == Setting::kAuto, "auto");
  Check(ParseSetting("xbox", setting) && setting == Setting::kXbox, "xbox");
  Check(ParseSetting("playstation", setting) && setting == Setting::kPlayStation, "playstation");
  Check(ParseSetting(" PlayStation ", setting) && setting == Setting::kPlayStation,
        "case and spaces ignored");
  Check(ParseSetting("PS4", setting) && setting == Setting::kPlayStation, "ps4 alias");
  Check(ParseSetting("dualshock4", setting) && setting == Setting::kPlayStation, "dualshock4 alias");
  setting = Setting::kXbox;
  Check(!ParseSetting("switch", setting) && setting == Setting::kXbox, "unknown value unchanged");
  Check(!ParseSetting("", setting), "empty value unknown");
}

void LabelTests() {
  const auto& labels = PlayStationLabels();
  // The SDK maps SDL's face buttons by position: south is A.
  Equal(labels.at("a"), "Cross", "A is Cross");
  Equal(labels.at("b"), "Circle", "B is Circle");
  Equal(labels.at("x"), "Square", "X is Square");
  Equal(labels.at("y"), "Triangle", "Y is Triangle");
  Equal(labels.at("lb"), "L1", "LB");
  Equal(labels.at("rb"), "R1", "RB");
  Equal(labels.at("lt"), "L2", "LT");
  Equal(labels.at("rt"), "R2", "RT");
  Equal(labels.at("start"), "Options", "Start");
  Equal(labels.at("back"), "Touchpad", "Back is the touchpad");
  Check(!labels.contains("analogup") && !labels.contains("leftanalog") && !labels.contains("dpad"),
        "sticks and d-pad keep their icons");
}

void ReplaceTests() {
  Equal(Replace("Press <a> to jump."), "Press [Cross] to jump.", "single tag");
  Equal(Replace("Press <a>, <b>, <x> or <y> in any combination."),
        "Press [Cross], [Circle], [Square] or [Triangle] in any combination.", "face buttons");
  Equal(Replace("<yellow>Press <rb><white>. <br> Hold <x> for the log."),
        "<yellow>Press [R1]<white>. <br> Hold [Square] for the log.", "colour and line tags kept");
  Equal(Replace("Press <lt> <analogright><analogleft> <analogup><analogup>."),
        "Press [L2] <analogright><analogleft> <analogup><analogup>.", "jutsu motions keep icons");
  Equal(Replace("Press <lb> to open the inventory, <start> to pause, <back> for the map."),
        "Press [L1] to open the inventory, [Options] to pause, [Touchpad] for the map.",
        "shoulder and menu buttons");
  Equal(Replace("Steer with <leftanalog>, pick with <dpad>."),
        "Steer with <leftanalog>, pick with <dpad>.", "group tags keep icons");
  Equal(Replace("<x-left> <x> <x>"), "<analogleft>+[Square] [Square] [Square]",
        "combo tag is the stick icon and the button");
  Equal(Replace("<y-up> <y> <x>"), "<analogup>+[Triangle] [Triangle] [Square]", "combo tag up");
  Equal(Replace("<x-right> <x> <x> <x> <y>"),
        "<analogright>+[Square] [Square] [Square] [Square] [Triangle]", "combo tag right");
  Equal(Replace("<z-left> <x-sideways> <x->"), "<z-left> <x-sideways> <x->",
        "unknown combo parts kept");
  Equal(Replace("Coins <goldcoin> <ancientcoin> <happy> <quest>"),
        "Coins <goldcoin> <ancientcoin> <happy> <quest>", "non-button tags kept");
  Equal(Replace("<A> <x"), "<A> <x", "case-sensitive, unterminated kept");
  Equal(Replace("a > b < c"), "a > b < c", "stray brackets kept");
  Equal(Replace("Sakura's <b>"), "Sakura's [Circle]", "UTF-8-safe ASCII around tags");
  Equal(Replace(""), "", "empty text");
  Equal(ReplaceButtonTags("Press <a>.", {}), "Press <a>.", "no labels, no change");
  Equal(Replace("Pressione <a> para pular."), "Pressione [Cross] para pular.",
        "translated text keeps working");
}

void ShoulderTests() {
  Equal(ReplaceShoulderTags("Press <lb> to open the inventory."),
        "Press \xC2\x8B to open the inventory.", "LB is the L1 glyph");
  Equal(ReplaceShoulderTags("<rb>Throw Kunai"), "\xC2\x8EThrow Kunai", "RB is the R1 glyph");
  Equal(ReplaceShoulderTags("Hold <lt> and <rt>, then <a> <x-left> <analogup>"),
        "Hold <lt> and <rt>, then <a> <x-left> <analogup>", "other tags stay icons");
  Equal(ReplaceShoulderTags("<LB> <lb"), "<LB> <lb", "case-sensitive, unterminated kept");
  Equal(ReplaceShoulderTags(""), "", "empty text");
}
}  // namespace

int main() {
  try {
    SettingTests();
    LabelTests();
    ReplaceTests();
    ShoulderTests();
    std::cout << "pad prompts PASS checks=" << checks << '\n';
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "pad prompts FAIL after " << checks << " checks: " << error.what() << '\n';
    return 1;
  }
}
