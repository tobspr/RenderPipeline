
#include "PSSMHelper.h"

/*

#include <Eigen/Dense>


void generate_equations(Eigen::MatrixXf &eq_system, Eigen::VectorXf &eq_results, const LVector4f &vec, LVector4f expected, int offset) {
    int write_offset = offset * 4;

    for (int row = 0; row < 4; ++row) {
        float expected_coeff = expected.get_cell(row);
        int col_offset = row * 4;
        for (int col = 0; col < 4; ++col) {
            eq_system(write_offset, col_offset + col) = vec.get_cell(col);
        }

        eq_results(write_offset++) = expected_coeff;
    }
}


LMatrix4f PSSMHelper::find_projection_mat(
            const LVector4f &near_ul,
            const LVector4f &near_ur,
            const LVector4f &near_ll,
            const LVector4f &near_lr,
   
            const LVector4f &far_ul,
            const LVector4f &far_ur,
            const LVector4f &far_ll,
            const LVector4f &far_lr) {



    // We have 8*4 = 32 equations, which require 16 coefficients each
    Eigen::MatrixXf equation_system(32, 16);
    Eigen::VectorXf equation_results(32);
    equation_system.fill(0);

    // Generate the equations
    int offset = 0;
    generate_equations(equation_system, equation_results, near_ul, LVector4f(-1,  1, 0, 1), offset++);
    generate_equations(equation_system, equation_results, near_ur, LVector4f( 1,  1, 0, 1), offset++);
    generate_equations(equation_system, equation_results, near_ll, LVector4f(-1, -1, 0, 1), offset++);
    generate_equations(equation_system, equation_results, near_lr, LVector4f( 1, -1, 0, 1), offset++);

    generate_equations(equation_system, equation_results, far_ul,  LVector4f(-1,  1, 1, 1), offset++);
    generate_equations(equation_system, equation_results, far_ur,  LVector4f( 1,  1, 1, 1), offset++);
    generate_equations(equation_system, equation_results, far_ll,  LVector4f(-1, -1, 1, 1), offset++);
    generate_equations(equation_system, equation_results, far_lr,  LVector4f( 1, -1, 1, 1), offset++);


    // cout << "Equation system: " << endl << equation_system << endl;
    // cout << "Coeff vector: " << endl << equation_results << endl;

    // Solve equation system
    Eigen::VectorXf solved_system = equation_system.colPivHouseholderQr().solve(equation_results);

    // cout << "Solved system: " << endl << solved_system << endl;

    // Construct result matrix and return it
    LMatrix4f result(
            solved_system(0), solved_system(4), solved_system(8), solved_system(12), 
            solved_system(1), solved_system(5), solved_system(9), solved_system(13), 
            solved_system(2), solved_system(6), solved_system(10), solved_system(14), 
            solved_system(3), solved_system(7), solved_system(11), solved_system(15)
        );
    return result;
}


*/