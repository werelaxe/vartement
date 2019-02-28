/* handwritten stdlib */

template <long long ...T>
struct __nan {
    const static unsigned long long value = -9223372036854775807;
};

template<long long A, long long B>
struct __add {
    const static long long value = A + B;
};

template<long long A, long long B>
struct __sub {
    const static long long value = A - B;
};

template<long long A, long long B>
struct __div {
    const static long long value = A / B;
};

template<long long A, long long B>
struct __mul {
    const static long long value = A * B;
};

template<long long A, long long B>
struct __mod {
    const static long long value = A % B;
};

template <long long ...T>
struct __list_ {};

template <long long H, long long ...T>
struct __list_<H, T...> {
    static const long long head = H;
    using tail = __list_<T...>;
    static const size_t length = 1 + sizeof...(T);
};

template <>
struct __list_<> {
    static const size_t length = 0;
};

template <long long ...T>
struct __list {
    using type = __list_<T...>;
};

template <typename LIST>
struct __head {
    static const long long value = LIST::head;
};

template <typename LIST>
struct __tail {
    using type = typename LIST::tail;
};

template <typename LIST>
struct __size {
    static const long long value = LIST::length;
};

template <long long H, typename TL>
struct __cons_ {};

template <long long H, long long ...T>
struct __cons_<H, __list_<T...>> {
    using type = __list_<H, T...>;
};

template <long long H, typename LIST>
struct __cons {
    using type = typename __cons_<H, LIST>::type;
};

template <long long H, typename TL>
struct __append_ {};

template <long long H, long long ...T>
struct __append_<H, __list_<T...>> {
    using type = __list_<T..., H>;
};

template <typename LIST, long long H>
struct __append {
    using type = typename __append_<H, LIST>::type;
};

template <typename LISTA, typename LISTB>
struct __concat_ {};

template <long long ...A, long long ...B>
struct __concat_<__list_<A...>, __list_<B...>> {
    using type = __list_<A..., B...>;
};

template <typename LISTA, typename LISTB>
struct __concat {
    using type = typename __concat_<LISTA, LISTB>::type;
};

template <typename LISTA, typename LISTB>
struct __lieq {};

template <>
struct __lieq<__list_<>, __list_<>> {
    static const long long value = 1;
};

template <long long H, long long ...TAIL>
struct __lieq<__list_<H, TAIL...>, __list_<>> {
    static const long long value = 0;
};

template <long long H, long long ...TAIL>
struct __lieq< __list_<>, __list_<H, TAIL...>> {
    static const long long value = 0;
};

template <long long HA, long long ...TAILA, long long HB, long long ...TAILB>
struct __lieq<__list_<HA, TAILA...>, __list_<HB, TAILB...>> {
    static const long long head_equals = HA == HB;
    static const long long value = (__list_<TAILA...>::length == __list_<TAILB...>::length) ?
    (head_equals ? __lieq<__list_<TAILA...>, __list_<TAILB...>>::value : 0) : 0;
};

template <long long A, long long B>
struct __eq {
    static const long long value = A == B;
};

template <long long A, long long B>
struct __neq {
    static const long long value = A != B;
};

template <long long A>
struct __not {
    static const long long value = !A;
};

template <long long A>
struct __bnot {
    static const long long value = ~A;
};

template <long long A, long long B>
struct __and {
    static const long long value = A && B;
};

template <long long A, long long B>
struct __band {
    static const long long value = A & B;
};

template <long long A, long long B>
struct __or {
    static const long long value = A || B;
};

template <long long A, long long B>
struct __bor {
    static const long long value = A | B;
};

template <long long A, long long B>
struct __xor {
    static const long long value = A ^ B;
};

template <long long A>
struct __bool {
    static const long long value = !!A;
};

template <long long A, long long B>
struct __lshift {
    static const long long value = A << B;
};

template <long long A, long long B>
struct __rshift {
    static const long long value = A >> B;
};

template <long long A, long long B>
struct __lt {
    static const long long value = A < B;
};

template <long long A, long long B>
struct __leq {
    static const long long value = A <= B;
};

template <long long A, long long B>
struct __gt {
    static const long long value = A > B;
};

template <long long A, long long B>
struct __geq {
    static const long long value = A >= B;
};

template <long long STMT, long long A, long long B>
struct __if {
    static const long long value = (STMT ? A : B);
};

template <long long STMT, typename A, typename B>
struct __tif {
    using type = A;
};

template <typename A, typename B>
struct __tif<0, A, B> {
    using type = B;
};


/* generated stdlib */

template<typename lst, long long x, long long acc>
struct __count_ {
    const static long long value =
        __if<
            __eq<__head<lst>::value, x>::value,
            __count_<typename __tail<lst>::type, x, __add<acc, 1>::value>::value,
            __count_<typename __tail<lst>::type, x, acc
        >::value>::value;
};

template<long long x, long long acc>
struct __count_<__list<>::type, x, acc> {
    const static long long value = acc;
};

template<typename lst, long long x>
struct __count {
    const static long long value = __count_<lst, x, 0>::value;
};

template<typename lst, long long x>
struct __contains {
    const static long long value = __if<__eq<__head<lst>::value, x>::value, 1, __contains<typename __tail<lst>::type, x>::value>::value;
};

template<long long x>
struct __contains<__list<>::type, x> {
    const static long long value = 0;
};

template<long long x, long long y>
struct __max {
    const static long long value = x > y ? x : y;
};

template<long long x, long long y>
struct __min {
    const static long long value = x > y ? y : x;
};

template<typename lst, long long i>
struct __get {
    const static long long value = __if<i, __get<typename __tail<lst>::type, __sub<i, 1>::value>::value, __head<lst>::value>::value;
};

template<typename lst>
struct __get<lst, -1> {
    const static long long value = __nan<>::value;
};

template<typename lst>
void __print() {
    cout << lst::head << " ";
    __print<typename lst::tail>();
}

template<>
void __print<__list_<>>() {
    cout << endl;
}

template<long long x>
void __print() {
    cout << x << endl;
}

template<typename lst, template<long long x> typename func>
struct __map {
    using type = typename __cons<func<__head<lst>::value>::value, typename __map<typename __tail<lst>::type, func>::type>::type;
};

template<template<long long x> typename func>
struct __map<typename __list<>::type, func> {
    using type = typename __list<>::type;
};
