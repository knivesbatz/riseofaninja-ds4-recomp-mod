#include "mods/pad_prompts.h"

#include <array>
#include <utility>

namespace narutorise::pad_prompts {
namespace {

// The button tags of the English text tables (mods/key_prompts.cpp) and the
// DualShock 4 button in each one's place. Names rather than symbols: the
// game's fonts lack the cross, circle, square and triangle glyphs.
constexpr std::pair<std::string_view, std::string_view> kButtons[] = {
    {"a", "Cross"},  {"b", "Circle"}, {"x", "Square"},  {"y", "Triangle"},
    {"lb", "L1"},    {"rb", "R1"},    {"lt", "L2"},     {"rt", "R2"},
    {"start", "Options"},            {"back", "Touchpad"},
};

// The directions of the combo tags ("<x-left>"), each also a stick tag of its
// own ("<analogleft>") that draws the same direction without a button.
constexpr std::array<std::string_view, 4> kDirections = {"up", "down", "left", "right"};

bool EqualsNoCase(std::string_view a, std::string_view b) {
  if (a.size() != b.size())
    return false;
  for (size_t i = 0; i < a.size(); ++i) {
    char x = a[i], y = b[i];
    if (x >= 'A' && x <= 'Z')
      x = char(x - 'A' + 'a');
    if (y >= 'A' && y <= 'Z')
      y = char(y - 'A' + 'a');
    if (x != y)
      return false;
  }
  return true;
}

bool IsDirection(std::string_view name) {
  for (const auto direction : kDirections) {
    if (name == direction)
      return true;
  }
  return false;
}

}  // namespace

bool ParseSetting(std::string_view value, Setting& out) {
  while (!value.empty() && (value.front() == ' ' || value.front() == '\t'))
    value.remove_prefix(1);
  while (!value.empty() && (value.back() == ' ' || value.back() == '\t'))
    value.remove_suffix(1);
  if (EqualsNoCase(value, "auto")) {
    out = Setting::kAuto;
  } else if (EqualsNoCase(value, "xbox")) {
    out = Setting::kXbox;
  } else if (EqualsNoCase(value, "playstation") || EqualsNoCase(value, "ps4") ||
             EqualsNoCase(value, "dualshock4")) {
    out = Setting::kPlayStation;
  } else {
    return false;
  }
  return true;
}

const key_prompts::Labels& PlayStationLabels() {
  static const key_prompts::Labels labels = [] {
    key_prompts::Labels out;
    for (const auto& [tag, label] : kButtons)
      out.emplace(std::string(tag), std::string(label));
    return out;
  }();
  return labels;
}

std::string ReplaceButtonTags(std::string_view text, const key_prompts::Labels& labels) {
  const auto find = [&](std::string_view key) -> const std::string* {
    const auto found = labels.find(key);
    return found == labels.end() ? nullptr : &found->second;
  };
  // The replacement of one tag; empty when it stays as it is.
  const auto replace = [&](std::string_view name) -> std::string {
    // Combo input: a direction held with a button ("<x-left>").
    if (const size_t dash = name.find('-'); dash != std::string_view::npos) {
      const auto* button = find(name.substr(0, dash));
      const auto direction = name.substr(dash + 1);
      if (!button || !IsDirection(direction))
        return {};
      return "<analog" + std::string(direction) + ">+[" + *button + "]";
    }
    const auto* label = find(name);
    return label ? "[" + *label + "]" : std::string{};
  };

  std::string out;
  out.reserve(text.size());
  size_t at = 0;
  while (at < text.size()) {
    const size_t open = text.find('<', at);
    if (open == std::string_view::npos)
      break;
    const size_t close = text.find('>', open + 1);
    if (close == std::string_view::npos)
      break;
    out.append(text.substr(at, open - at));
    const auto replacement = replace(text.substr(open + 1, close - open - 1));
    if (!replacement.empty())
      out += replacement;
    else
      out.append(text.substr(open, close - open + 1));
    at = close + 1;
  }
  out.append(text.substr(at));
  return out;
}

std::string ReplaceShoulderTags(std::string_view text) {
  static const key_prompts::Labels glyphs = {{"lb", std::string(kL1Glyph)},
                                             {"rb", std::string(kR1Glyph)}};
  std::string out;
  out.reserve(text.size());
  size_t at = 0;
  while (at < text.size()) {
    const size_t open = text.find('<', at);
    if (open == std::string_view::npos)
      break;
    const size_t close = text.find('>', open + 1);
    if (close == std::string_view::npos)
      break;
    out.append(text.substr(at, open - at));
    const auto found = glyphs.find(text.substr(open + 1, close - open - 1));
    if (found != glyphs.end())
      out += found->second;
    else
      out.append(text.substr(open, close - open + 1));
    at = close + 1;
  }
  out.append(text.substr(at));
  return out;
}

}  // namespace narutorise::pad_prompts
