"""Build local PS2 v0.4.46 over v0.4.45 with matching footer typography."""
from build_ps2_turn_funds import build
from fix_ps2_objective_footer import patch
from verify_ps2_objective_footer import verify

if __name__=='__main__':
    build('0.4.46','0.4.45','objective_footer',patch,verify)
