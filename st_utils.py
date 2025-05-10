import streamlit as st
import pandas as pd
import numpy as np

# --- 常量 ---
# 定义支持的轴参数和输出指标
supported_axis_params = {
    "WACC": "wacc", 
    "退出乘数 (EBITDA)": "exit_multiple", 
    "永续增长率": "perpetual_growth_rate"
}
supported_output_metrics = { 
    "每股价值": "value_per_share",
    "企业价值 (EV)": "enterprise_value",
    "股权价值": "equity_value",
    "EV/EBITDA (初期)": "ev_ebitda", 
    "终值现值/EV 比例": "tv_ev_ratio"
}

# --- 辅助函数 ---
# Helper function to generate axis values (更新版，处理 None/NaN 更健壮)
def generate_axis_values(center, step, points):
    # Ensure points is an odd number >= 3
    if not isinstance(points, int) or points < 1:
        points = 3
    elif points % 2 == 0:
        points += 1
        
    # Ensure center and step are valid numbers (handle None or NaN)
    try:
        center = float(center)
        if np.isnan(center): center = 0.0
    except (TypeError, ValueError):
        center = 0.0
    
    try:
        step = float(step)
        if np.isnan(step): step = 0.01
    except (TypeError, ValueError):
        step = 0.01

    offset = (points - 1) // 2
    return [center + step * (i - offset) for i in range(points)]

# Helper function to find the closest index for highlighting (更新版，处理类型和NaN)
def find_closest_index(value_list, target_value):
    """Finds the index of the value in the list closest to the target value."""
    if target_value is None or not value_list:
        return None
    try:
        target_float = float(target_value)
        if np.isnan(target_float): return None
        # Ensure list values are floats for comparison
        value_list_float = np.array(value_list).astype(float)
        if np.isnan(value_list_float).any(): # Handle NaN in the list itself if necessary
             # Option 1: Ignore NaNs in list (find closest among non-NaNs) - more complex
             # Option 2: Return None if list contains NaN (simpler)
             # Let's choose Option 2 for now, or handle based on expected data
             pass # Assuming list should not contain NaN for sensitivity axis
        diffs = np.abs(value_list_float - target_float) 
        return np.argmin(diffs)
    except (ValueError, TypeError):
        return None

# Helper function to apply styling for the center cell (更新版，略微调整边界检查)
def highlight_center_cell_apply(df, center_row_idx, center_col_idx, color='background-color: #fcf8e3'):
    """Applies styling to the center cell based on calculated indices."""
    style_df = pd.DataFrame('', index=df.index, columns=df.columns)
    if center_row_idx is not None and center_col_idx is not None:
        # Ensure indices are within DataFrame bounds
        if 0 <= center_row_idx < df.shape[0] and 0 <= center_col_idx < df.shape[1]:
            style_df.iloc[center_row_idx, center_col_idx] = color
    return style_df

# Helper function to generate unique formatted labels for sensitivity table axes
def get_unique_formatted_labels(original_float_values, param_type_key):
    is_percent_type = param_type_key in ["wacc", "perpetual_growth_rate"]
    
    precisions = [2, 3, 4, 5, 6] if is_percent_type else [1, 2, 3, 4] # Decimal places to try
    suffix = "%" if is_percent_type else "x"

    for p_val in precisions:
        current_labels = []
        for val in original_float_values:
            if pd.isna(val):
                current_labels.append("-") # Placeholder for NaNs
            else:
                if is_percent_type:
                    current_labels.append(f"{val * 100:.{p_val}f}{suffix}") # Multiply by 100 for %
                else:
                    current_labels.append(f"{val:.{p_val}f}{suffix}")
        
        # Check uniqueness among non-"-" labels
        actual_labels_to_check = [lbl for lbl in current_labels if lbl != "-"]
        if len(set(actual_labels_to_check)) == len(actual_labels_to_check):
            return current_labels # Return as soon as unique labels are found
            
    # Last resort: if increasing precision didn't help, append index to duplicates
    # This uses the highest precision from the loop for the base string formatting
    final_labels_with_highest_precision = []
    highest_p = precisions[-1]
    for val in original_float_values:
        if pd.isna(val):
            final_labels_with_highest_precision.append("-")
        else:
            if is_percent_type:
                final_labels_with_highest_precision.append(f"{val * 100:.{highest_p}f}{suffix}")
            else:
                final_labels_with_highest_precision.append(f"{val:.{highest_p}f}{suffix}")

    # Make unique by appending counter to duplicates
    unique_final_labels = []
    counts = {}
    for lbl in final_labels_with_highest_precision:
        # Handle NaNs: they don't need unique counters among themselves for this purpose,
        # but Styler might still have issues if the placeholder "-" is considered non-unique 
        # in a list of all "-", though that's unlikely to be the source of the error here.
        # The main goal is to make actual data point labels unique.
        if lbl == "-": 
            unique_final_labels.append("-") 
            continue

        if lbl in counts:
            counts[lbl] += 1
            unique_final_labels.append(f"{lbl} ({counts[lbl]})") # e.g., "2.50% (1)"
        else:
            counts[lbl] = 0 # Initialize count for this label
            unique_final_labels.append(lbl)
    return unique_final_labels

# --- 回调函数：更新敏感性分析UI元素 ---
# 注意：此函数依赖 st.session_state，因此如果要在 streamlit_app.py 之外使用，
# 需要确保 st 对象可用，或者通过参数传递 session_state。
# 目前，为了简化，暂时不移动此回调函数，因为它深度耦合了 Streamlit 的 session_state。
# 如果需要移动，则需要重构其与 session_state 的交互方式。
# def update_sensitivity_ui_elements():
#     # ... (implementation from streamlit_app.py) ...
#     pass
