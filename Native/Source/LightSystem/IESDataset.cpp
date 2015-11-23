
#include "IESDataset.h"

IESDataset::IESDataset() {

}

IESDataset::~IESDataset() {

}

void IESDataset::set_vertical_angles(const PTA_float &vertical_angles) {
    nassertv(vertical_angles.size() > 0);
    cout << "Setting " << vertical_angles.size() << " vertical angles .. " << endl;

	_vertical_angles = vertical_angles;
}

void IESDataset::set_horizontal_angles(const PTA_float &horizontal_angles) {
    nassertv(horizontal_angles.size() > 0);
    cout << "Setting " << horizontal_angles.size() << " horizontal angles .. " << endl;

	_horizontal_angles = horizontal_angles;
}

void IESDataset::set_candela_values(const PTA_float &candela_values) {
	nassertv(candela_values.size() == _horizontal_angles.size() * _vertical_angles.size());
	_candela_values = candela_values;
	cout << get_candela_value(3, 0);
}

float IESDataset::get_candela_value(size_t vertical_angle_idx, size_t horizontal_angle_idx) {
	size_t index = vertical_angle_idx + horizontal_angle_idx * _vertical_angles.size();
	nassertr(index >= 0 && index < _candela_values.size(), 0.0);
	return _candela_values[index];
}
