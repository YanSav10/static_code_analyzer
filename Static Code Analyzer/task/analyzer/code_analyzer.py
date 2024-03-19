import os
import sys
import re
import ast


def check_line_length(line):
    return "S001" if len(line.rstrip()) > 79 else ""


def check_indentation(line):
    return "S002" if line.startswith(" ") and (len(line) - len(line.lstrip(' '))) % 4 != 0 else ""


def check_unnecessary_semicolon(line):
    line_without_strings_and_comments = re.sub(r'"(\\.|[^"\\])*"|\'(\\.|[^\'\\])*\'|(#.*)', '', line)
    return "S003" if ';' in line_without_strings_and_comments else ""


def check_inline_comment_spacing(line):
    if '#' in line and not line.strip().startswith('#'):
        code, comment = line.split('#', 1)
        if not code.endswith('  ') and code.strip():
            return "S004"
    return ""


def check_todo_comment(line):
    if '#' in line:
        comment_part = line.split('#', 1)[1]
        if 'todo' in comment_part.lower():
            return "S005"
    return ""


def check_construction_spaces(line):
    match = re.match(r' *(class|def)\s{2,}', line)
    if match:
        construction = match.group(1)
        return f"S007 Too many spaces after '{construction}'"
    return ""


def check_class_naming(line):
    match = re.match(r'class\s+([A-Za-z_]\w*)(\s*\(.*\))?:', line)
    if match:
        class_name = match.group(1)
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name):
            return f"S008 Class name '{class_name}' should use CamelCase"
    return ""


class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self, filepath):
        self.issues = []
        self.filepath = filepath

    def visit_FunctionDef(self, node):
        func_name = node.name
        if not func_name.startswith('__') and not re.match(r'^_?[a-z]+[a-z0-9_]*(_[a-z0-9]+)*_?$', func_name):
            self.issues.append((self.filepath, node.lineno, f"S009 Function name '{func_name}' should use snake_case"))

        for arg in node.args.args:
            if not re.match(r'^_?[a-z]+[a-z0_]*(_[a-z0-9]+)*_?$', arg.arg):
                self.issues.append(
                    (self.filepath, node.lineno, f"S010 Argument name '{arg.arg}' should be written in snake_case"))

        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.issues.append((self.filepath, node.lineno, "S012 The default argument value is mutable"))

        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                if not re.match(r'^_?[a-z]+[a-z0_]*(_[a-z0-9]+)*_?$', var_name):
                    self.issues.append(
                        (self.filepath, node.lineno, f"S011 Variable '{var_name}' should be written in snake_case"))
        self.generic_visit(node)


def analyze_ast(filepath, issues):
    with open(filepath, "r", encoding="utf-8") as source:
        tree = ast.parse(source.read(), filename=filepath)
        analyzer = CodeAnalyzer(filepath)
        analyzer.visit(tree)
        issues.extend(analyzer.issues)


def analyze_file_content(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    issues = []
    blank_line_count = 0
    for line_num, line in enumerate(lines, start=1):
        if line.strip() == "":
            blank_line_count += 1
        else:
            if blank_line_count > 2:
                issues.append((filepath, line_num, "S006 More than two blank lines used before this line"))
            blank_line_count = 0

        for check in [check_line_length, check_indentation, check_unnecessary_semicolon,
                      check_inline_comment_spacing, check_todo_comment, check_construction_spaces,
                      check_class_naming]:
            result = check(line)
            if result:
                issues.append((filepath, line_num, result))

    analyze_ast(filepath, issues)  # AST-based checks
    return issues


def analyze_path(path):
    issues = []
    if os.path.isfile(path) and path.endswith('.py'):
        issues.extend(analyze_file_content(path))
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    issues.extend(analyze_file_content(file_path))
    return issues


def main():
    if len(sys.argv) != 2:
        return

    path = sys.argv[1]
    issues = analyze_path(path)

    issues_sorted = sorted(issues, key=lambda issue: (os.path.abspath(issue[0]), issue[1], issue[2]))

    for filepath, line_num, issue in issues_sorted:
        print(f"{filepath}: Line {line_num}: {issue}")


if __name__ == "__main__":
    main()
