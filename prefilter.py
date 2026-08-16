import yaml
import os
import re
import sys
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Rule:
    category: str
    severity: str
    pattern: str
    description: str
    hard_block: bool
    _regex: re.Pattern

    @classmethod
    def from_dict(cls, data: dict) -> 'Rule':
        return cls(
            category=data['category'],
            severity=data['severity'],
            pattern=data['pattern'],
            description=data['description'],
            hard_block=data.get('hard_block', False),
            _regex=re.compile(data['pattern'])
        )

@dataclass
class PrefilterResult:
    status: str  # 'SAFE', 'NEEDS_REVIEW', 'BLOCKED'
    rule: Optional[Rule] = None

class Prefilter:
    def __init__(self, rules_file: str = None):
        if rules_file is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            rules_file = os.path.join(script_dir, "risk_rules.yaml")
        self.rules: List[Rule] = []
        self._load_rules(rules_file)

    def _load_rules(self, path: str):
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            for rule_data in data.get('rules', []):
                self.rules.append(Rule.from_dict(rule_data))

    def analyze(self, command: str) -> PrefilterResult:
        command = command.strip()
        command_no_sudo = re.sub(r'^sudo\s+', '', command)
        
        severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        best_rule = None
        best_severity = 0
        
        for rule in self.rules:
            if rule._regex.search(command) or rule._regex.search(command_no_sudo):
                current_sev = severity_map.get(rule.severity.upper(), 0)
                if current_sev > best_severity:
                    best_severity = current_sev
                    best_rule = rule

        if best_rule:
            if best_rule.hard_block:
                return PrefilterResult(status='BLOCKED', rule=best_rule)
            return PrefilterResult(status='NEEDS_REVIEW', rule=best_rule)
            
        return PrefilterResult(status='SAFE')

if __name__ == "__main__":
    test_commands = [
        "rm -rf /",
        "rm -rf /tmp/build_cache",
        "rm -rf /etc",
        "rm -rf /home/user/old_project",
        "sudo systemctl stop networking",
        "sudo rm -rf /important_dir",
        "dd if=/dev/zero of=/dev/sda",
        "ls -la"
    ]
    
    prefilter = Prefilter()
    print("Testing Prefilter Standalone\n")
    for cmd in test_commands:
        res = prefilter.analyze(cmd)
        if res.status == 'SAFE':
            print(f"[SAFE] {cmd}")
        else:
            block_status = "BLOCKED (Hard)" if res.status == 'BLOCKED' else "NEEDS_REVIEW"
            print(f"[{block_status}] {cmd}")
            print(f"  -> Category: {res.rule.category}, Severity: {res.rule.severity}")
            print(f"  -> Reason: {res.rule.description}\n")
