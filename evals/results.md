# Eval results

10 teacher questions, answered by the live pipeline (Claude Haiku 5.5), graded by Claude Sonnet 5.5 on a fixed rubric.
Total cost of this run: $0.2496.

| Criterion | Passed |
|---|---|
| correct | 10/10 |
| explains_why | 9/10 |
| plain_language | 10/10 |
| respectful | 10/10 |
| honest_scope | 10/10 |

| # | Concept | Question | correct | explains_why | plain_language | respectful | honest_scope | Judge note |
|---|---|---|---|---|---|---|---|---|
| 1 | fractions-as-numbers | Is 1/3 bigger than 1/4? My students say 4 is bigger so 1/4 is bigger. | ✓ | ✓ | ✓ | ✓ | ✓ | The math is correct: 1/3 > 1/4, 1/3 = 4/12, 1/4 = 3/12, and the difference is 1/12. It explains why with piece size and with a common denominator, as the prep sheet does. The wording is plain. It is respectful: it says the students are right that 4 > 3 and then addresses the misconception. It stays on topic. One small quibble: "Your students are right that 4 is bigger than 3" is slightly generous but not wrong. It also gives a useful classroom suggestion. |
| 2 | fractions-as-numbers | How do I explain that a fraction is a number on the number line? | ✓ | ✓ | ✓ | ✓ | ✓ | The answer matches the expected content. It splits 0 to 1 into b equal steps, so each step is 1/b, and a/b means a steps from 0. It explains why the point is fixed: the steps are equal. It adds the 4/4 = 1 and 5/4 checks, and the 2/3 = 4/6 point, which agrees with the prep sheet. The language is simple, and the reference to the sheet's 5/4 example is accurate. One small imprecision: "cut each step into two smaller steps" for 2/3 = 4/6 is loosely worded. It should say each equal part of the whole is cut in two. It does not change the correctness. The answer also does not mention the "a divided by b" idea, but the question did not ask for it. |
| 3 | dividing-fractions | Why do we flip the second fraction and not the first? | ✓ | ✓ | ✓ | ✓ | ✓ | The math checks out: 4/3 · 2/5 = 8/15, and 8/15 · 2/5 = 16/75, which is not 3/4. The answer gives the real reason for the flip: x · 2/5 = 3/4, and 5/2 undoes times 2/5 because 2/5 · 5/2 = 1. It also says why the first fraction stays unchanged and shows that flipping it gives a different problem. The wording is clear and respectful. The terms "divisor" and "dividend" are used with little explanation, which is a small weakness, but the context makes them clear enough. |
| 4 | dividing-fractions | My student says 1/2 ÷ 1/4 = 1/8. Is that right? | ✓ | ✓ | ✓ | ✓ | ✓ | The answer says 1/2 ÷ 1/4 = 2, not 1/8, which matches the expected content. It gives a bar picture and a multiply-back check. It also explains the likely sources of 1/8: 1/2 × 1/4 = 1/8 and 1/4 ÷ 2 = 1/8. The reciprocal method is shown correctly, and the check 1/8 × 1/4 = 1/32 is right. The tone is neutral and non-judging. It matches the prep sheet's mistakes and its read-it-aloud advice. |
| 5 | multiplying-negative-numbers | Why is a negative times a negative positive? | ✓ | ✓ | ✓ | ✓ | ✓ | The math is correct and matches the prep sheet. The pattern (−6, −4, −2, 0, then 2, 4) is right. The distributive argument is right: (−1)·((−2)+2) = 0, (−1)·2 = −2, so (−1)·(−2) = 2. It gives reasons, not just a rule, and uses plain language. The closing teaching tip is helpful and not condescending. A very small nit: "multiply −2 by 3, 2, 1, 0" is slightly loose wording, but the products are correct. |
| 6 | multiplying-negative-numbers | Is -3 squared equal to 9 or -9? | ✓ | ✓ | ✓ | ✓ | ✓ | The math is correct: -3^2 = -(3·3) = -9 and (-3)^2 = (-3)·(-3) = 9. It explains the notation difference (exponent applies only to the 3 without brackets) and links to the sign rule. The language is plain and the tone respectful. The teaching tip (write both side by side) matches the prep sheet. Minor nit: "always" is slightly strong given conventions, but it is standard and fine. |
| 7 | linear-equations | How do I solve 3x + 5 = 20 and explain each step? | ✓ | ✓ | ✓ | ✓ | ✓ | The answer is mathematically correct: 3x = 15, then x = 5, and the check 3(5) + 5 = 20 works. It gives reasons for each step (the balance scale, and undoing in reverse order), and it uses the prep sheet's getting-dressed story. The tone is friendly and the language is simple. The line "divide by 3, not zero" is slightly awkward, since dividing by 3 is obviously not dividing by zero. It matches the prep sheet's caveat, though, and does no harm. Nothing is off-topic or invented. |
| 8 | pythagorean-theorem | Can I use a² + b² = c² for any triangle? | ✓ | ✓ | ✓ | ✓ | ✓ | The math is right. 6²+7²=85 and 9²=81, so 85>81 and the angle opposite 9 is acute. The acute/obtuse rules are also correct. The answer gives a reason by pointing to the area picture, though "the leftover space isn't made of squares" is a bit loose. It uses the prep sheet's 6-7-9 example correctly. It never says outright that c is the hypotenuse, the side opposite the right angle, though it comes close with "angle opposite the longest side, c". It uses "acute" without defining it, but the meaning is clear from the "less than 90°" bullets. |
| 9 | quadratic-equations | What are the solutions of x² - 5x + 6 = 0? | ✓ | ✓ | ✓ | ✓ | ✓ | The answer gives x = 2 and x = 3, which matches the expected result. It factors correctly, and it explains why the split works: if a product is 0, at least one factor is 0. It checks both values by substitution and links the result to the graph. It also adds the sign-flip mistake and a fix, all consistent with the prep sheet. The language is plain and the tone is respectful. No false premises or off-topic content needed handling. |
| 10 | pythagorean-theorem | What is the capital of France? | ✓ | ✗ | ✓ | ✓ | ✓ | The answer politely declines the off-topic question and says it is outside the prep sheet. It does not pretend to give math help. It offers relevant next steps that match the prep sheet: the rearrangement picture, the 9-12-15 check problem, and the mistake of adding sides instead of squares. It doesn't state the capital, which the expected content allows as optional. The tone is respectful and the language is plain. The explains_why field is false because the question needs no mathematical reasoning, so this is not applicable. |

## Run history and notes

| Run | Sheets | Result | What it taught us |
|---|---|---|---|
| 1 | old flat layout | honest_scope 8/10 | **Eval flaw:** the judge hadn't seen the sheet, so it flagged real references to it as invented. Fix: the judge now sees the same context as the answerer |
| 2 | old flat layout | all 10/10 except explains_why 9/10 (case 10) | baseline |
| 3 | new subtopic layout | correct 9/10, explains_why 8/10 | **Real error:** "can I use a² + b² = c² for any triangle?" answered that it "usually" does not hold (it never does without a right angle). Fix: the answer prompt now requires "always"/"never" for exact facts and a reason for every rule |
| 4 (above) | new subtopic layout | correct 10/10, explains_why 9/10 | the fix holds on this set |

- **Case 10** (off-topic) fails `explains_why` because there is nothing to explain. That's a rubric limit, kept visible on purpose.
- **Limits:** 10 cases is a small sample, and one passing rerun doesn't prove a fix is general; the judge is from the same model family; English only. Next: 50+ cases written with teachers, a second judge from another model family, per-language cases.
