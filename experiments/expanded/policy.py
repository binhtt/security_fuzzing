"""Separate generic policy from each task's requested action."""
def install(s):
    original=s.prompts
    def prompts(case,role,source,tagged=True):
        system,user=original(case,role,source,tagged)
        if 'policy_text' in case:
            old='Policy: '+s.POLICY_TEXT[case['family']]
            assert old in system
            system=system.replace(old,'Policy: '+case['policy_text'])
        return system,user
    s.prompts=prompts
