class AnonymousClass1 {
    /** Java Language Notes:
     *
     * Anonymous classes always extend superclass or implements interfaces
     * anonymous class cannot implement multiple interfaces
     * uses: assigned to variables or sent to functions as parameter
     * The syntax of an anonymous class expression is like the invocation of a constructor,
     *   except that there is a class definition contained in a block of code
     * syntax: new ClassInterfaceName ( constructorParameters ) { **code: class declaration body** }
     * Because an anonymous class definition is an expression, it must be part of a statement.
     *
     **/

    @Override
    protected ResourcePager<Issue> createPager() {
        return new IssuePager(store) {
            @Override
            public PageIterator<Issue> createIterator(int page, int size) {
                return service.pageIssues(repository, filter.toFilterMap(),
                        page, size);
            }
        };
    }

    public int f(java.util.AClass aClass, java.util.AClass bClass) {
        return 2;
    }

    public int callF() {
        java.util.BClass b = new java.util.BClass() {};
        return f(new java.util.AClass() {}, b);
    }

    private void refreshIssue() {
        getSherlockActivity().setSupportProgressBarIndeterminateVisibility(true);

        new RefreshIssueTask(getActivity(), repositoryId, issueNumber,
                bodyImageGetter, commentImageGetter) {

            @Override
            protected void onException(Exception e) throws RuntimeException {
                super.onException(e);

                ToastUtils.show(getActivity(), e, string.error_issue_load);
                ViewUtils.setGone(progress, true);

                getSherlockActivity().setSupportProgressBarIndeterminateVisibility(false);
            }

            @Override
            protected void onSuccess(FullIssue fullIssue) throws Exception {
                super.onSuccess(fullIssue);

                if (!isUsable())
                    return;

                issue = fullIssue.getIssue();
                comments = fullIssue;
                updateList(fullIssue.getIssue(), fullIssue);

                getSherlockActivity().setSupportProgressBarIndeterminateVisibility(false);
            }
        }.execute();

    }

}
