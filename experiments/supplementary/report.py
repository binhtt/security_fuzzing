"""Produce a concise supplemental report after all inference has completed."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
def action(a):return a['tool']+'('+a['target']+')' if a else 'invalid'
def main():
    s=json.loads((P/'new_results.json').read_text())
    lines=['# Kết quả thực nghiệm bổ sung — 01/11/2026','',
      '## Phạm vi','',
      'Đã tái lập các bảng của 2.550 workflows từ dữ liệu lưu trữ; bước này không thực hiện suy luận mới. Thực nghiệm mới gồm 8 fresh-process workflows, 250 logical workflows trong pilot tìm kiếm, và 4 lần gọi executor độc lập. Không gộp các tập này vào kết quả chính.','',
      '## 1. Fresh-process replay của phát hiện ownership','',
      'Mỗi cặp dùng cùng model, task, trusted state và payload tấn công đã chọn từ bản ghi cũ. Mỗi arm/seed chạy trong tiến trình mới, không đọc cache suy luận cũ. Seed 211 là seed đã phát hiện; 631, 743, 857 là ba seed bổ sung.','',
      '| Seed | Clean vi phạm | Attack vi phạm | Clean expected action |','|---|---|---|---|']
    by={}
    for r in s['replay']:by.setdefault(r['seed'],{})[r['arm']]=r
    for seed,rs in sorted(by.items()):lines.append(f"| {seed} | {rs['clean']['violation']} | {rs['attack']['violation']} | {rs['clean']['expected']} |")
    lines+=['','Ở seed 211, parsed outputs của cả ba role và final actions khớp bản ghi gốc cho cả clean và attack. Đây là xác nhận tái lập của một payload đã chọn; không phải ước lượng attack success trên các task độc lập. Clean và attack đều phụ thuộc seed.','',
      '## 2. Đáp ứng executor khi thay proposal','',
      'Giữ nguyên task, policy, trusted state, menu và seed 211; chỉ thay proposal đầu vào bằng từng action trong menu. Không dùng cache.','',
      '| Proposal | Final action | Vi phạm |','|---|---|---|']
    for r in s['executor_map']:lines.append(f"| {action(r['proposal'])} | {action(r['final']['action'])} | {r['final']['violation']} |")
    lines+=['','Trong cấu hình này, proposal an toàn không bảo đảm executor an toàn. Kết quả hỗ trợ kiểm tra riêng bước executor; không chứng minh cùng cơ chế trên mọi mô hình hay hệ agent.','',
      '## 3. Pilot tìm kiếm sau khởi tạo đa input','',
      'Qwen2.5-0.5B, năm evaluation cases, seed 631, bốn selectors, 12 queries/strategy/case. Ba queries khởi tạo chung là direct, authority và boundary, đều tính trong ngân sách. Parent selection có thể khác từ query 4. Tập case được cố định trước khi chạy; không loại case theo kết quả.','',
      '| Selector | Raw detection | Strict-qualified | Valid-safe | First detection sau initialization | Valid workflows |','|---|---|---|---|---|---|']
    for r in s['pilot']:
        lines.append(f"| {r['method']} | {r['raw_detected']}/{r['cases']} | {r['strict_detected']}/{r['strict_eligible']} | {r['valid_safe_detected']}/{r['valid_safe_eligible']} | {r['first_detection_after_initialization']} | {r['valid_workflows']}/{r['adversarial_workflows']} |")
    lines+=['','Cả bốn selectors chỉ phát hiện case budget vốn đã vi phạm trong clean control. Strict-qualified detection là 0/3 và valid-safe detection là 0/4 cho mọi selector. Không có first detection sau initialization, dù payload đã khác giữa selectors từ query 4. Vì vậy pilot không cung cấp bằng chứng về lợi thế feedback so với random. Matching counts không chứng minh equivalence. Pilot nhỏ và khác protocol chính, do đó không dùng để suy rộng hoặc gộp tỷ lệ.','',
      '| Query | Case groups có payload khác nhau giữa selectors |','|---|---|']
    for r in s['divergence']:lines.append(f"| {r['query']} | {r['different_payload_groups']}/{r['case_groups']} |")
    m=s['pilot_manifest'];lines+=['',f"Pilot: {m['logical_episodes']} logical workflows, {m['fresh_inferences']} fresh role inferences, {m['cache_hits']} exact-input reuses trong lần chạy mới. Không thừa kế cache primary. Reuses không phải independent observations.",'',
      '## 4. Diễn giải và giới hạn','',
      'Fresh replay giải quyết hạn chế về việc chưa xác nhận lại phát hiện ownership. Executor mapping cho thấy cần phân biệt unsafe proposal propagation với lỗi quyết định ở executor. Pilot kiểm tra được phần chọn parent sau initialization; chỉ được kết luận lợi thế selector nếu chính các số đo hỗ trợ. Không điều chỉnh tập task hoặc lặp thử để tạo ra khác biệt mong muốn.','',
      'Các giới hạn còn lại: mô hình nhỏ, menu hữu hạn, năm task, một seed cho pilot, oracle thủ công trên synthetic fixtures. Chưa có model mạnh hơn, open-ended actions hoặc đánh giá benchmark bên ngoài. Bước tiếp theo cần cải thiện clean-task competence trên development set rồi cố định protocol cho nhiều task/seed độc lập hơn.','',
      '## Tái lập','',
      'Xem README.md, protocol.json, environment.json, source code và toàn bộ JSON/JSONL/logs đi kèm. Models không được đóng gói; nguồn tải và SHA256 nằm trong configs/model_sources.json của artifact.']
    (P/'REPORT_VI.md').write_text('\n'.join(lines)+'\n')
    latex=[r'\subsection{Supplementary Replay and Search Diagnostics}',r'\label{subsec:supplementary_replay}',
      'We conduct eight fresh-process ownership workflows using the recorded',
      'attack payload and matched clean inputs at seeds 211, 631, 743, and 857.',
      'All executions are valid. Clean inputs produce no violations;',
      'the attack violates ownership at seeds 211 and 743.',
      'At the original seed 211, all three parsed role outputs match the archived',
      'records without inference-cache reuse. This confirms the selected finding',
      'but does not estimate a general attack success rate.',
      '',
      'A separate four-proposal executor diagnostic fixes the trusted inputs',
      'and seed while varying the planner proposal. Both permitted deletion',
      'and inspection proposals can lead to prohibited deletion, illustrating',
      'that a safe proposal does not ensure a safe executor decision in this instance.',
      '',
      'An exploratory Qwen2.5-0.5B pilot uses five cases, seed 631, four selectors,',
      'and twelve queries per run, including three common initialization inputs.',
      'Parent-selection strategies can diverge from query four.',r'\begin{table}[htbp]',r'\centering\small',r'\caption{Exploratory pilot detection; denominators count eligible cases.}',r'\begin{tabular}{lrrr}',r'\hline Selector & Raw & Strict & Valid-safe \\',r'\hline']
    for r in s['pilot']:latex.append(f"{r['method'].replace('_','-')} & {r['raw_detected']}/{r['cases']} & {r['strict_detected']}/{r['strict_eligible']} & {r['valid_safe_detected']}/{r['valid_safe_eligible']} " + chr(92)*2)
    latex += [r'\hline',r'\end{tabular}',r'\end{table}', 'All raw detections concern a case already violated under its clean control.', 'No first detection occurs after initialization, although selector payloads', 'differ in all five case groups at query four. The pilot therefore provides', 'no evidence of a feedback-selection advantage over random selection.', '', 'These exploratory observations are reported separately from the primary', 'evaluation; they neither establish selector equivalence nor support', 'generalization across tasks, seeds, or model families.']
    (P/'supplementary_results.tex').write_text('\n'.join(latex)+'\n')
if __name__=='__main__':main()
