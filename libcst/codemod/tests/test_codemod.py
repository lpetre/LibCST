# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
from unittest import expectedFailure

import libcst as cst
import libcst.matchers as m
from libcst.codemod import Codemod, CodemodContext, CodemodTest, SkipFile, RemoveFile


class SimpleCodemod(Codemod):
    def __init__(self, context: CodemodContext, *, skip: bool = False, remove: bool = False) -> None:
        super().__init__(context)
        self.skip = skip
        self.remove = remove

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        if self.skip:
            raise SkipFile()
        elif self.remove:
            raise RemoveFile()
        else:
            return tree


class TestSkipRemoveDetection(CodemodTest):

    TRANSFORM = SimpleCodemod
    SIMPLE_CODE = """
        def foo() -> None:
            pass

        def bar() -> int:
            return 5
    """

    def test_detect_skip(self) -> None:
        code = self.SIMPLE_CODE
        self.assertCodemod(code, code)
        self.assertCodemod(code, code, skip=True, expected_skip=True)

    def test_detect_remove(self) -> None:
        code = self.SIMPLE_CODE
        self.assertCodemod(code, code)
        self.assertCodemod(code, code, remove=True, expected_remove=True)

    @expectedFailure
    def test_did_not_skip_but_should(self) -> None:
        code = self.SIMPLE_CODE
        self.assertCodemod(code, code, expected_skip=True)

    @expectedFailure
    def test_did_not_remove_but_should(self) -> None:
        code = self.SIMPLE_CODE
        self.assertCodemod(code, code, expected_remove=True)

    @expectedFailure
    def test_skipped_but_should_not(self) -> None:
        code = self.SIMPLE_CODE
        self.assertCodemod(code, code, skip=True, expected_skip=False)

    @expectedFailure
    def test_removed_but_should_not(self) -> None:
        code = self.SIMPLE_CODE
        self.assertCodemod(code, code, remove=True, expected_remove=False)


class IncrementCodemod(Codemod):
    def __init__(self, context: CodemodContext, *, iterations: int) -> None:
        super().__init__(context)
        self.iterations = iterations

    def should_allow_multiple_passes(self) -> bool:
        return True

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        if self.iterations == 0:
            return tree
        self.iterations -= 1

        return cst.ensure_type(
            m.replace(
                tree,
                m.Integer(),
                lambda node, _: node.with_changes(value=str(int(node.value) + 1)),
            ),
            cst.Module,
        )


class TestMultipass(CodemodTest):

    TRANSFORM = IncrementCodemod

    def test_multi_iterations(self) -> None:
        before = """
            x = 5
        """
        after = """
            x = 10
        """

        self.assertCodemod(before, after, iterations=5)
