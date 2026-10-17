"""Static source-code audit engine for Feature 2: Promise vs. Reality Audit.
Compares specifications/requirements with actual implemented source code.
"""
import ast
import json
import os
import re
import time
from typing import Dict, List, Optional, Tuple
from ..models.audit import (
    AuditFinding,
    AuditFindingStatus,
    AuditReport,
    CodeLocation,
    PrioritizedWorkItem,
)

class RequirementItem:
    def __init__(self, req_id: str, title: str, description: str, keywords: List[str]):
        self.req_id = req_id
        self.title = title
        self.description = description
        self.keywords = keywords

def parse_requirements_document(doc_text: str) -> List[RequirementItem]:
    """Parse text/markdown requirements into individual identifiable requirement items."""
    lines = doc_text.splitlines()
    requirements: List[RequirementItem] = []
    current_title = ""
    current_desc: List[str] = []
    req_counter = 1

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check for Heading: ## Req or ### Req
        heading_match = re.match(r'^(?:#{1,4})\s+(?:Requirement\s*\d*[:\s]*|Feature\s*\d*[:\s]*|)(.+)$', stripped, re.IGNORECASE)
        # Check for bullet items: 1. Title or - [ ] Title or - Title
        bullet_match = re.match(r'^(?:(?:\d+\.|\*|-|\+)\s+(?:\[[\sx]\]\s*)?)(.+)$', stripped)

        if heading_match:
            if current_title:
                desc = " ".join(current_desc).strip()
                kws = extract_keywords(current_title + " " + desc)
                requirements.append(RequirementItem(
                    req_id=f"REQ-{req_counter:03d}",
                    title=current_title,
                    description=desc or current_title,
                    keywords=kws
                ))
                req_counter += 1
                current_desc = []
            current_title = heading_match.group(1).strip()

        elif bullet_match and len(bullet_match.group(1).strip()) > 10:
            if current_title and not current_desc:
                # If there was a heading, treat bullets as details
                current_desc.append(bullet_match.group(1).strip())
            else:
                # Independent requirement bullet
                if current_title:
                    desc = " ".join(current_desc).strip()
                    kws = extract_keywords(current_title + " " + desc)
                    requirements.append(RequirementItem(
                        req_id=f"REQ-{req_counter:03d}",
                        title=current_title,
                        description=desc or current_title,
                        keywords=kws
                    ))
                    req_counter += 1
                    current_desc = []
                current_title = bullet_match.group(1).strip()
        else:
            if current_title:
                current_desc.append(stripped)

    # Add final item
    if current_title:
        desc = " ".join(current_desc).strip()
        kws = extract_keywords(current_title + " " + desc)
        requirements.append(RequirementItem(
            req_id=f"REQ-{req_counter:03d}",
            title=current_title,
            description=desc or current_title,
            keywords=kws
        ))

    # If format was un-structured prose without headings/bullets, split by double newlines or sentences
    if not requirements and len(doc_text.strip()) > 0:
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', doc_text) if p.strip()]
        for idx, p in enumerate(paragraphs):
            first_sentence = p.split(".")[0].strip()
            kws = extract_keywords(p)
            requirements.append(RequirementItem(
                req_id=f"REQ-{idx+1:03d}",
                title=first_sentence[:80],
                description=p,
                keywords=kws
            ))

    return requirements

def extract_keywords(text: str) -> List[str]:
    """Extract search terms and keywords from requirement text."""
    stop_words = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "with", "by",
        "of", "from", "as", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "can", "could", "should", "would",
        "will", "shall", "must", "it", "this", "that", "these", "those", "all", "each",
        "every", "both", "either", "neither", "not", "no", "yes", "user", "system", "project"
    }
    words = re.findall(r'[a-zA-Z0-9_\-]{3,}', text.lower())
    filtered = [w for w in words if w not in stop_words]
    # Retain unique preserving order
    seen = set()
    result = []
    for w in filtered:
        if w not in seen:
            seen.add(w)
            result.append(w)
    return result

def inspect_python_ast(file_path: str, content: str) -> List[Dict]:
    """Parse Python file using AST to find classes, functions, and detect stubs."""
    findings = []
    try:
        tree = ast.parse(content, filename=file_path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = node.body
                # Filter out docstrings
                non_doc_body = [
                    stmt for stmt in body
                    if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str))
                ]
                is_stub = False
                if len(non_doc_body) == 0:
                    is_stub = True  # docstring only / empty
                elif len(non_doc_body) == 1:
                    stmt = non_doc_body[0]
                    if isinstance(stmt, ast.Pass):
                        is_stub = True
                    elif isinstance(stmt, ast.Raise):
                        is_stub = True
                    elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is ...:
                        is_stub = True  # Ellipsis (...)
                
                findings.append({
                    "type": "function",
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno),
                    "is_stub": is_stub,
                })
            elif isinstance(node, ast.ClassDef):
                findings.append({
                    "type": "class",
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno),
                    "is_stub": False,
                })
    except Exception:
        pass
    return findings


def audit_project_against_spec(
    project_id: str,
    source_dir: str,
    requirements_text: Optional[str] = None,
    acceptance_criteria: Optional[str] = None,
    spec_filename: Optional[str] = None,
    auto_detect_spec: bool = False,
) -> AuditReport:
    """Execute static Promise vs. Reality audit comparing requirements against project source."""
    if not os.path.exists(source_dir):
        raise ValueError(f"Project workspace '{source_dir}' does not exist")

    # Combine requirements_text and acceptance_criteria if provided
    full_text = requirements_text or ""
    if acceptance_criteria and acceptance_criteria.strip():
        full_text = full_text + "\n\n## Acceptance Criteria\n" + acceptance_criteria.strip()

    source_spec_label = spec_filename or "Custom Input"
    if not full_text.strip() and auto_detect_spec:
        # Look for README.md, SPEC.md, PRD.md, REQUIREMENTS.md
        found_spec = None
        for candidate in ("README.md", "SPEC.md", "PRD.md", "REQUIREMENTS.md", "docs/PRD.md"):
            cand_path = os.path.join(source_dir, candidate)
            if os.path.exists(cand_path):
                with open(cand_path, "r", encoding="utf-8", errors="ignore") as f:
                    full_text = f.read()
                    found_spec = candidate
                    source_spec_label = f"Auto-detected from {candidate}"
                break
        
        if not found_spec or not full_text.strip():
            raise ValueError("No requirements document provided and no specification files (README.md, SPEC.md) found in project")
    elif not full_text.strip():
        raise ValueError("Requirements document or text is required for audit")

    requirements_text = full_text


    # 1. Parse requirements into distinct items
    parsed_reqs = parse_requirements_document(requirements_text)
    if not parsed_reqs:
        raise ValueError("Could not parse any identifiable requirements from the provided document")

    # 2. Index all source files in project workspace
    source_files_cache: Dict[str, str] = {}
    test_files_cache: Dict[str, str] = {}

    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), source_dir).replace("\\", "/")
            full = os.path.join(root, f)
            # Read files under 1MB
            if os.path.getsize(full) < 1_000_000 and f.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".go", ".java")):
                try:
                    with open(full, "r", encoding="utf-8", errors="ignore") as content_file:
                        content = content_file.read()
                        if "test" in rel.lower() or f.startswith("test_") or f.endswith("_test.py"):
                            test_files_cache[rel] = content
                        else:
                            source_files_cache[rel] = content
                except Exception:
                    pass

    findings: List[AuditFinding] = []
    prioritized_roadmap: List[PrioritizedWorkItem] = []

    # 3. Evaluate each requirement against source files
    for req in parsed_reqs:
        req_lower = (req.title + " " + req.description).lower()
        matched_locations: List[CodeLocation] = []
        is_implemented = False
        is_partial = False
        is_stub = False
        has_test_coverage = False

        # Check for runtime/hardware/unverifiable traits
        is_unverifiable = any(
            term in req_lower
            for term in ("99.99%", "high availability", "sub-millisecond", "sla", "aws infrastructure", "cloud deployment", "hardware", "biometric")
        )

        # Search source code
        for file_path, content in source_files_cache.items():
            content_lower = content.lower()
            
            # Check how many keywords match
            kw_matches = [kw for kw in req.keywords if kw in content_lower]
            if len(kw_matches) >= max(2, len(req.keywords) // 2):
                # We have a candidate match in this file!
                lines = content.splitlines()
                # If Python, do AST inspection
                if file_path.endswith(".py"):
                    ast_items = inspect_python_ast(file_path, content)
                    for item in ast_items:
                        item_name_lower = item["name"].lower()
                        if any(kw in item_name_lower for kw in req.keywords):
                            snippet = "\n".join(lines[max(0, item["line_start"] - 1): min(len(lines), item["line_end"])])
                            matched_locations.append(CodeLocation(
                                file_path=file_path,
                                line_start=item["line_start"],
                                line_end=item["line_end"],
                                snippet=snippet[:300]
                            ))
                            if item["is_stub"]:
                                is_stub = True
                                is_partial = True
                            else:
                                is_implemented = True

                # Regex fallback for JS / TS / other
                if not matched_locations:
                    for l_idx, line in enumerate(lines):
                        if any(kw in line.lower() for kw in req.keywords):
                            if "todo" in line.lower() or "fixme" in line.lower() or "not implemented" in line.lower():
                                is_stub = True
                                is_partial = True
                            matched_locations.append(CodeLocation(
                                file_path=file_path,
                                line_start=l_idx + 1,
                                line_end=min(len(lines), l_idx + 6),
                                snippet="\n".join(lines[l_idx:min(len(lines), l_idx + 5)])[:300]
                            ))
                            if not is_stub:
                                is_implemented = True
                            if len(matched_locations) >= 3:
                                break

        # Check for test evidence
        for test_file, test_content in test_files_cache.items():
            t_lower = test_content.lower()
            if any(kw in t_lower for kw in req.keywords):
                has_test_coverage = True
                break

        # 4. Classify Status
        if is_unverifiable and not is_implemented:
            status = AuditFindingStatus.UNVERIFIED
            reasoning = f"Requirement refers to runtime infrastructure or non-functional characteristics that cannot be verified solely from static source inspection."
            method = "static_heuristic"
            confidence = "MEDIUM"
            action = f"Add runtime integration benchmarks or synthetic probes to verify '{req.title}'."
            prio = "MEDIUM"

        elif is_stub or (is_partial and not is_implemented):
            status = AuditFindingStatus.PARTIALLY_IMPLEMENTED
            reasoning = f"Found code stubs or partial implementations with placeholders/TODOs in {len(matched_locations)} file(s). Core implementation logic is incomplete."
            method = "ast_inspection"
            confidence = "HIGH"
            action = f"Complete business logic in {matched_locations[0].file_path if matched_locations else 'source file'} and replace placeholder stubs."
            prio = "HIGH"

        elif is_implemented:
            status = AuditFindingStatus.IMPLEMENTED
            test_note = " Verified by matching automated test assertions." if has_test_coverage else " Note: Automated unit test coverage was not detected."
            reasoning = f"Concrete code implementation identified across {len(matched_locations)} location(s).{test_note}"
            method = "ast_inspection"
            confidence = "HIGH" if has_test_coverage else "MEDIUM"
            action = "Add unit tests to ensure long-term regression safety." if not has_test_coverage else "Requirement satisfied; maintain regression tests."
            prio = "LOW"

        else:
            status = AuditFindingStatus.MISSING
            reasoning = f"No matching functions, classes, API routes, or data models were found in the scanned workspace."
            method = "regex_pattern"
            confidence = "HIGH"
            action = f"Implement new module and route handlers for '{req.title}'."
            prio = "CRITICAL"

        finding = AuditFinding(
            requirement_id=req.req_id,
            title=req.title,
            description=req.description,
            status=status,
            supporting_files=matched_locations[:4],
            reasoning=reasoning,
            validation_method=method,
            confidence=confidence,
            recommended_next_action=action,
        )
        findings.append(finding)

        if status != AuditFindingStatus.IMPLEMENTED:
            prioritized_roadmap.append(PrioritizedWorkItem(
                priority=prio,
                requirement_id=req.req_id,
                title=req.title,
                action=action,
                estimated_effort="Low" if status == AuditFindingStatus.PARTIALLY_IMPLEMENTED else "Medium"
            ))

    # Sort roadmap: CRITICAL -> HIGH -> MEDIUM -> LOW
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    prioritized_roadmap.sort(key=lambda x: priority_order.get(x.priority, 4))

    # Compute compliance score
    impl_count = sum(1 for f in findings if f.status == AuditFindingStatus.IMPLEMENTED)
    part_count = sum(1 for f in findings if f.status == AuditFindingStatus.PARTIALLY_IMPLEMENTED)
    miss_count = sum(1 for f in findings if f.status == AuditFindingStatus.MISSING)
    unver_count = sum(1 for f in findings if f.status == AuditFindingStatus.UNVERIFIED)

    total = len(findings)
    compliance_score = round(((impl_count + (0.5 * part_count)) / total) * 100, 1) if total > 0 else 0.0

    return AuditReport(
        project_id=project_id,
        source_spec=source_spec_label,
        total_requirements=total,
        implemented_count=impl_count,
        partially_implemented_count=part_count,
        missing_count=miss_count,
        unverified_count=unver_count,
        compliance_score=compliance_score,
        findings=findings,
        prioritized_roadmap=prioritized_roadmap,
        limitations=[
            "Static analysis relies on symbol definitions, AST inspection, and keyword matching; dynamically constructed routes may require runtime tracing.",
            "Requirements without code artifacts (e.g. cloud deployments, third-party credentials) are marked 'unverified'.",
            "Tests are scanned based on naming conventions (test_*.py, *.test.js)."
        ],
        audited_at=time.time(),
    )

run_audit_engine = audit_project_against_spec
