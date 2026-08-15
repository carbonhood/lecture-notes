---
type: "lecture-transcript"
source_note: "[[2026-08-15_Week3_Linear_Algebra]]"
---

Okay, good morning everyone. Today is week three of linear algebra, and we're going to talk about matrix multiplication and how it relates to linear transformations.

First, a quick recall. A matrix is just a rectangular array of numbers. If A is m by n, that means it has m rows and n columns. A vector in R n is an n by one column, and when we write A times x, we're applying the linear map represented by A.

Let's be precise about multiplication. Suppose A is m by n and B is n by p. Then the product C equals A B is m by p, and the i j entry of C is the sum from k equals one to n of a i k times b k j. In other words, each entry is a row-dot-column.

Why does the inner dimension have to match? Because you're pairing the length of a row of A with the length of a column of B. If those lengths disagree, the product is undefined.

Here's a two-by-two example. Let A be the matrix with first row one, two and second row three, four. Let B be the matrix with first row zero, one and second row one, zero. Then A B has first row two, one and second row four, three. Check the one one entry: one times zero plus two times one equals two.

Now, linear transformations. A map T from R n to R m is linear if T of u plus v equals T of u plus T of v, and T of c u equals c times T of u for any scalar c. Once you pick the standard basis, every linear map has a unique matrix A such that T of x equals A x.

Composition of transformations becomes matrix multiplication. If S of y equals B y and T of x equals A x, then S of T of x equals B A x. Order matters. In general A B is not equal to B A.

Eigenstuff preview for next week, just so the vocabulary is familiar. If A v equals lambda v for some nonzero vector v, we call v an eigenvector and lambda an eigenvalue. Geometrically, A stretches or flips that direction without rotating it off its line.

Key intuition to leave with: multiplying by a matrix is not "just arithmetic on a grid." It is applying a linear transformation, and the algebra of matrices is the algebra of those maps composed together.

Any questions before we do the worksheet? Alright, let's work problem one on page forty-two.
