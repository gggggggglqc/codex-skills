#!/bin/bash

# safe-rm.sh - 安全的rm命令包装器，实现权限检查功能

set -euo pipefail

# 调试函数
debug() {
    if [[ "${DEBUG:-}" == "1" ]]; then
        echo "[DEBUG] $*" >&2
    fi
}

# 错误输出函数
error() {
    echo "[ERROR] $*" >&2
}

# 获取绝对路径
get_absolute_path() {
    if [[ -d "$1" ]]; then
        (cd "$1" && pwd)
    elif [[ -f "$1" ]]; then
        result=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
        echo "$result"
    else
        # 对于不存在的路径，尝试解析其父目录
        local dir
        dir="$(dirname "$1")"
        if [[ -d "$dir" ]]; then
            echo "$(cd "$dir" && pwd)/$(basename "$1")"
        else
            echo "$1"
        fi
    fi
}

# 检查路径是否被保护
is_protected() {
    local target="$1"
    local policy="$2"  # deny, ask, allow
    local tool_name="$3"  # Read, Edit, MultiEdit

    # 权限配置根目录
    local permission_root="${HOME}/.qoder/permission-match-for-bash/${tool_name}/${policy}"
    local gitignore_file="${permission_root}/.gitignore"

    debug "Checking protection for $target with policy $policy and tool $tool_name"
    debug "Gitignore file: $gitignore_file"

    # 检查.gitignore文件是否存在
    if [[ ! -f "$gitignore_file" ]]; then
        debug "Gitignore file not found, target is not protected"
        return 1
    fi

    # 确保是git仓库
    if ! git -C "$permission_root" rev-parse --is-inside-work-tree &> /dev/null; then
        debug "Initializing git repository in $permission_root"
        git -C "$permission_root" init -q &> /dev/null || {
            error "Failed to initialize git repository"
            return 1
        }
    fi

    # 获取绝对路径并转换为相对路径（去掉开头的/)
    local abs_path
    abs_path=$(get_absolute_path "$target")
    local rel_path="${abs_path#/}"

    debug "Absolute path: $abs_path"
    debug "Relative path: $rel_path"

    # 使用git check-ignore检查是否匹配
    if git -C "$permission_root" check-ignore -q --no-index "$rel_path"; then
        debug "Path $rel_path is protected by $gitignore_file"
        return 0
    else
        debug "Path $rel_path is not protected by $gitignore_file"
        return 1
    fi
}

# 主函数
main() {
    # 如果没有参数，直接调用真正的rm
    if [[ $# -eq 0 ]]; then
        command rm "$@"
        return $?
    fi

    # 解析参数，收集要删除的文件路径
    local files_to_check=()
    local rm_args=()
    local arg

    # 跳过所有flag参数，只收集文件路径
    while [[ $# -gt 0 ]]; do
        arg="$1"
        case "$arg" in
            -i|-f|-r|-R|--recursive|--force|--interactive|--one-file-system|--no-preserve-root|--preserve-root)
                # 这些是rm的flag参数，直接传递给rm
                rm_args+=("$arg")
                shift
                ;;
            --)
                # 结束参数解析
                shift
                # 剩余参数都是文件路径
                while [[ $# -gt 0 ]]; do
                    files_to_check+=("$1")
                    rm_args+=("$1")
                    shift
                done
                ;;
            -*)
                # 其他flag参数
                rm_args+=("$arg")
                shift
                ;;
            *)
                # 文件路径参数
                files_to_check+=("$arg")
                rm_args+=("$arg")
                shift
                ;;
        esac
    done

    debug "Files to check: ${files_to_check[*]}"
    debug "RM args: ${rm_args[*]}"

    # 检查每个文件是否被保护
    for file in "${files_to_check[@]}"; do
        # 检查拒绝规则
        if is_protected "$file" "deny" "Read" || \
           is_protected "$file" "deny" "Edit" || \
           is_protected "$file" "deny" "MultiEdit"; then
            error "Permission denied: $file is protected by Read or Edit  tools' deny rules, please check your CLI permission configuration. If you still want to remove it, please remove manually."
            return 1
        fi

    done

    # 如果没有被保护，则执行真正的rm命令
    debug "Executing: command rm ${rm_args[*]}"
    command rm "${rm_args[@]}"
    return $?
}

# 执行主函数
main "$@"