
#include "IESDataset.h"

IESDataset::IESDataset() {

}

IESDataset::~IESDataset() {

}

void IESDataset::set_vertical_angles(const PTA_float &vertical_angles) {
    nassertv(vertical_angles.size() > 0);
	_vertical_angles = vertical_angles;
}

void IESDataset::set_horizontal_angles(const PTA_float &horizontal_angles) {
    nassertv(horizontal_angles.size() > 0);
	_horizontal_angles = horizontal_angles;
}

void IESDataset::set_candela_values(const PTA_float &candela_values) {
	nassertv(candela_values.size() == _horizontal_angles.size() * _vertical_angles.size());
	_candela_values = candela_values;
}

float IESDataset::get_candela_value_from_index(size_t vertical_angle_idx, size_t horizontal_angle_idx) {
	size_t index = vertical_angle_idx + horizontal_angle_idx * _vertical_angles.size();
	nassertr(index >= 0 && index < _candela_values.size(), 0.0);
	return _candela_values[index];
}

float IESDataset::get_candela_value(float vertical_angle, float horizontal_angle) {

    // Special case for datasets without horizontal angles
    if (_horizontal_angles.size() == 1) {
        return get_vertical_candela_value(0, vertical_angle);
    }

    float max_angle = _horizontal_angles[_horizontal_angles.size() - 1];

    // Wrap angle to fit from 0 .. 360 degree. Most profiles only distribute
    // candela values from 0 .. 180 or even 0 .. 90. We have to mirror the
    // values at those borders (so 2 times for 180 degree and 4 times for 90 degree)
    horizontal_angle = fmod(horizontal_angle, 2.0f * max_angle);
    if (horizontal_angle > max_angle) {
        horizontal_angle = 2.0 * max_angle - horizontal_angle;
    }

    // Simlar to the vertical step, we now try interpolating a horizontal angle,
    // but we need to evaluate the vertical value for each row instead of fetching
    // the value directly
    for (size_t horizontal_index = 1; horizontal_index < _horizontal_angles.size(); ++horizontal_index) {
        float curr_angle = _horizontal_angles[horizontal_index];

        if (curr_angle >= horizontal_angle) {

            // Get previous angle data
            float prev_angle = _horizontal_angles[horizontal_index - 1];
            float prev_value = get_vertical_candela_value(horizontal_index - 1, vertical_angle);
            float curr_value = get_vertical_candela_value(horizontal_index, vertical_angle);

            // Interpolate lineary
            float lerp = (horizontal_angle - prev_angle) / (curr_angle - prev_angle);

            // Should never occur, but to be safe:
            if (lerp < 0.0 || lerp > 1.0) {
                cout << "ERROR: Invalid horizontal lerp: " << lerp << ", requested angle was " << horizontal_angle << ", prev = " << prev_angle << ", cur = " << curr_angle << endl;
            }

            return curr_value * lerp + prev_value * (1-lerp);
        }
    }

    return 0.0;
}

float IESDataset::get_vertical_candela_value(size_t horizontal_angle_idx, float vertical_angle) {
    nassertr(horizontal_angle_idx >= 0 && horizontal_angle_idx < _horizontal_angles.size(), 0.0);

    // Lower bound
    if (vertical_angle < 0.0) return 0.0;

    // Upper bound
    if (vertical_angle > _vertical_angles[_vertical_angles.size() - 1] ) return 0.0;

    // Find lowest enclosing angle
    for (size_t vertical_index = 1; vertical_index < _vertical_angles.size(); ++vertical_index) {
        float curr_angle = _vertical_angles[vertical_index];
        
        // Found value
        if (curr_angle > vertical_angle) {

            // Get previous angle data
            float prev_angle = _vertical_angles[vertical_index - 1];
            float prev_value = get_candela_value_from_index(vertical_index - 1, horizontal_angle_idx);
            float curr_value = get_candela_value_from_index(vertical_index, horizontal_angle_idx);

            // Interpolate lineary
            float lerp = (vertical_angle - prev_angle) / (curr_angle - prev_angle);

            // Should never occur, but to be safe:
            if (lerp < 0.0 || lerp > 1.0) {
                cout << "ERROR: Invalid vertical lerp: " << lerp << ", requested angle was " << vertical_angle << ", prev = " << prev_angle << ", cur = " << curr_angle << endl;
            }

            return curr_value * lerp + prev_value * (1-lerp);
        }
    }

    return 0.0;
}
