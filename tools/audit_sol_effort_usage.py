"""Recover model/effort and final cumulative usage for the Sol effort translators.

Reads only session metadata, turn context and token-count events into the audit.
No conversation text is copied. Run after translator follow-ups finish; --partial
is a read-only progress check. Estimates are Standard credits, not an invoice.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path

from update_review_sheet import save

ROOT_ID = '01a0fd06-d51e-7413-9cf2-976590635969'
EFFORTS = {'sol61low3': 'low', 'sol61med3': 'medium',
           'sol61high3': 'high', 'sol61xhigh3': 'xhigh'}
DEFAULT_SESSIONS = Path('C:/Users/Binh/.codex/sessions/2026/10/03')
TOKEN_FIELDS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
                'output_tokens', 'reasoning_output_tokens', 'total_tokens')


def collect(directories):
    agents = {}
    for directory in directories:
        for path in directory.glob('*.jsonl'):
            with path.open(encoding='utf-8') as stream:
                try:
                    first = json.loads(next(stream))
                except (ValueError, StopIteration):
                    continue
                meta = first.get('payload', {})
                source = meta.get('source')
                if not isinstance(source, dict):
                    continue
                spawn = source.get('subagent', {}).get('thread_spawn', {})
                if spawn.get('parent_thread_id') != ROOT_ID:
                    continue
                agent_path = spawn.get('agent_path', '')
                matched = [(tag, n) for tag in EFFORTS for n in range(5)
                           if agent_path == '/root/' + tag + '_slice_' + str(n)]
                if not matched:
                    continue
                tag, n = matched[0]
                settings, usage, records = set(), None, 0
                for line in stream:
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    payload = event.get('payload', {})
                    if event.get('type') == 'turn_context':
                        settings.add((payload.get('model'), payload.get('effort')))
                    if event.get('type') == 'event_msg' and payload.get('type') == 'token_count':
                        info = payload.get('info') or {}
                        if info.get('total_token_usage'):
                            usage = info['total_token_usage']
                            records += 1
                assert settings == {('gpt-6.1-sol', EFFORTS[tag])}, (agent_path, settings)
                if usage is None:
                    continue
                tokens = {k: usage.get(k, 0) for k in TOKEN_FIELDS}
                assert tokens['input_tokens'] + tokens['output_tokens'] == tokens['total_tokens']
                assert tokens['cached_input_tokens'] <= tokens['input_tokens']
                assert tokens['reasoning_output_tokens'] <= tokens['output_tokens']
                aid = meta['id']
                assert aid not in agents, 'Duplicate session encountered: ' + aid
                agents[aid] = dict(tag=tag, slice=n, agent_id=aid, agent_path=agent_path,
                                   rollout_path=str(path), model='gpt-6.1-sol', effort=EFFORTS[tag],
                                   usage_records=records, tokens=tokens)
    result = sorted(agents.values(), key=lambda a: (list(EFFORTS).index(a['tag']), a['slice']))
    assert len({(x['tag'], x['slice']) for x in result}) == len(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session-dir', type=Path, action='append')
    parser.add_argument('--partial', action='store_true')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    assert not (args.partial and args.write), 'Partial counts must not be saved as final.'
    agents = collect(args.session_dir or [DEFAULT_SESSIONS])
    aggregates = []
    for tag, effort in EFFORTS.items():
        chosen = [a for a in agents if a['tag'] == tag]
        if not args.partial:
            assert {a['slice'] for a in chosen} == set(range(5)), (tag, len(chosen))
        tokens = {k: sum(a['tokens'][k] for a in chosen) for k in TOKEN_FIELDS}
        uncached = tokens['input_tokens'] - tokens['cached_input_tokens']
        cost = (Decimal(uncached) * 50 + Decimal(tokens['cached_input_tokens']) * Decimal('2.5')
                + Decimal(tokens['output_tokens']) * 250) / 1000000
        aggregates.append(dict(tag=tag, model='gpt-6.1-sol', effort=effort, slices=len(chosen),
                               **tokens, uncached_input_tokens=uncached,
                               standard_credit_equivalent=float(cost)))
    result = dict(root_thread_id=ROOT_ID, audit_date='2026-10-03', partial=args.partial,
                  method='Final cumulative total_token_usage per distinct translator context, summed once; includes follow-up reviews; excludes coordinator.',
                  pricing_source='https://learn.chatgpt.com/docs/pricing',
                  credits_per_million=dict(input=50, cached_input=2.5, output=250),
                  pricing_basis='Standard credit-equivalent estimate, not actual billed credits or included subscription allowance.',
                  agents=agents, runs=aggregates)
    print(json.dumps(aggregates, indent=2))
    if args.write:
        save(Path('work/output/stage30s_sol_effort_token_usage.json'), result)
        print('Saved final metadata-only translator usage and estimated Standard credits.')


if __name__ == '__main__':
    main()
